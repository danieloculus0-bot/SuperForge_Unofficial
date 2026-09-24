from __future__ import annotations

import html
import json
from flask import Flask, jsonify, redirect, request, url_for

from .audit import tail_entries, verify_journal, record_event
from .context_menu import menu_for
from .db import db, init_db
from .schema_extensions import init_extensions
from .event_bus import logic_matrix, publish, register_default_logic
from .integrations.service import IntegrationService
from .modules.learning import patterns
from .modules.quality import create_quality_record, quality_pulse
from .ui import page

def e(value)->str:
    return html.escape("" if value is None else str(value))

def table_html(rows,columns,entity_type,label_field=None):
    if not rows:
        return "<div class='empty'>No records yet.</div>"
    out=["<table><thead><tr>"]
    out.extend(f"<th>{e(label)}</th>" for _,label in columns)
    out.append("</tr></thead><tbody>")
    for row in rows:
        d=dict(row)
        label=d.get(label_field or columns[0][0]) or f"{entity_type} {d.get('id','')}"
        out.append(f"<tr class='sf-context' data-entity-type='{e(entity_type)}' data-entity-id='{e(d.get('id'))}' data-entity-label='{e(label)}'>")
        for key,_ in columns:
            value=d.get(key)
            if key=="status":
                out.append(f"<td><span class='badge accent'>{e(value)}</span></td>")
            else:
                out.append(f"<td>{e(value)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)

def context_banner():
    ctype=request.args.get("context_type","")
    cid=request.args.get("context_id","")
    if not ctype or not cid:
        return ""
    return f"<div class='panel sf-context' data-entity-type='{e(ctype)}' data-entity-id='{e(cid)}' data-entity-label='{e(ctype)} {e(cid)}'><div class='statline'><b>Context:</b> {e(ctype)} #{e(cid)} <span>Cross-module filters are active where a direct relationship exists.</span></div></div>"

def _linked_id(source_table,source_id,field):
    with db() as con:
        row=con.execute(f"SELECT {field} FROM {source_table} WHERE id=?",(source_id,)).fetchone()
        return row[field] if row and row[field] is not None else None

def _list(sql,args=()):
    with db() as con:
        return con.execute(sql,args).fetchall()

def create_app(test_config:dict|None=None)->Flask:
    init_db()
    init_extensions()
    register_default_logic()
    app=Flask(__name__)
    app.config.update(SECRET_KEY="superforge-local")
    if test_config: app.config.update(test_config)

    @app.get("/")
    def dashboard():
        pulse=quality_pulse()
        with db() as con:
            counts={
                "jobs":con.execute("SELECT COUNT(*) n FROM jobs WHERE status!='closed'").fetchone()["n"],
                "po":con.execute("SELECT COUNT(*) n FROM purchase_orders WHERE status NOT IN ('closed','received')").fetchone()["n"],
                "inventory":con.execute("SELECT COUNT(*) n FROM inventory_items WHERE (on_hand-allocated)<=reorder_point").fetchone()["n"],
                "clocking":con.execute("SELECT COUNT(*) n FROM clocking_errors WHERE status!='closed'").fetchone()["n"],
                "actions":con.execute("SELECT COUNT(*) n FROM workflow_actions WHERE status='open'").fetchone()["n"],
            }
        cards=[
            ("Open Jobs",counts["jobs"],"/jobs"),("Open POs",counts["po"],"/purchase-orders"),
            ("Inventory Watch",counts["inventory"],"/inventory"),("Clocking Errors",counts["clocking"],"/clocking-errors"),
            ("Open Quality",pulse["open_quality"],"/quality"),("Workflow Actions",counts["actions"],"/planning"),
        ]
        body="<section class='page-head'><div class='grow'><p class='eyebrow'>One system. Shared context. Receipts for everything.</p><h1>Manufacturing command center</h1><p class='sub'>ERP, quality, maintenance, drawing control, FAI, PPAP, purchasing, inventory, clocking, planning and BEAN intelligence share one event and audit spine. Right-click any record to move through the related modules without losing context.</p></div><a class='button' href='/quality/new'>New Quality Record</a></section>"
        body+="<div class='grid'>"+"".join(f"<a class='card sf-context' style='text-decoration:none' href='{href}'><strong class='big'>{val}</strong><span class='label'>{e(label)}</span></a>" for label,val,href in cards)+"</div>"
        body+=f"<div class='panel' style='margin-top:14px'><h2>Quality pulse</h2><div class='statline'><span>Overdue: <b>{pulse['overdue']}</b></span><span>Open CARs: <b>{pulse['open_cars']}</b></span><span>Failed FAI: <b>{pulse['failed_fai']}</b></span><span>30-day PPM: <b>{'n/a' if pulse['ppm']['ppm'] is None else round(pulse['ppm']['ppm'],1)}</b></span></div></div>"
        return page("Command Center",body,module_key="")

    @app.route("/jobs",methods=["GET","POST"])
    def jobs():
        if request.method=="POST":
            job=request.form.get("job_number","").strip()
            if job:
                with db() as con:
                    cur=con.execute("INSERT INTO jobs(job_number,sales_order,quantity,due_date,status,current_operation,priority,notes) VALUES(?,?,?,?,?,?,?,?)",
                        (job,request.form.get("sales_order"),request.form.get("quantity") or None,request.form.get("due_date") or None,request.form.get("status") or "open",request.form.get("current_operation"),request.form.get("priority") or "normal",request.form.get("notes")))
                    rid=cur.lastrowid
                record_event(event_type="JOB_MUTATION",action="CREATE",module="job_tracker",entity_type="job",entity_id=rid,actor="local")
                publish("job.changed",source_module="job_tracker",entity_type="job",entity_id=str(rid),actor="local",payload={"job_number":job})
            return redirect("/jobs")
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="SELECT id,job_number,sales_order,quantity,due_date,status,current_operation,priority FROM jobs"; args=()
        if ctype=="purchase_order":
            jid=_linked_id("purchase_orders",cid,"job_id")
            if jid: sql+=" WHERE id=?"; args=(jid,)
        elif ctype=="quality_record":
            jid=_linked_id("quality_records",cid,"job_id")
            if jid: sql+=" WHERE id=?"; args=(jid,)
        elif ctype=="clocking_error":
            jid=_linked_id("clocking_errors",cid,"job_id")
            if jid: sql+=" WHERE id=?"; args=(jid,)
        elif ctype=="fai":
            jid=_linked_id("fai_runs",cid,"job_id")
            if jid: sql+=" WHERE id=?"; args=(jid,)
        sql+=" ORDER BY id DESC LIMIT 300"
        rows=_list(sql,args)
        form="""<details class='panel'><summary><b>Add job</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Job Number<input name='job_number' required></label><label>Sales Order<input name='sales_order'></label><label>Quantity<input name='quantity' type='number'></label>
<label>Due Date<input name='due_date' type='date'></label><label>Status<input name='status' value='open'></label><label>Current Operation<input name='current_operation'></label>
<label>Priority<input name='priority' value='normal'></label><label class='wide'>Notes<textarea name='notes'></textarea></label><div><button>Save Job</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>ERP / Production</p><h1>Job Tracker</h1><p class='sub'>Jobs are the common spine for quality, purchasing, inventory, clocking, FAI, documents and planning.</p></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("job_number","Job"),("sales_order","SO"),("quantity","Qty"),("due_date","Due"),("status","Status"),("current_operation","Operation"),("priority","Priority")],"job","job_number")+"</div>"
        return page("Job Tracker",body,module_key="job_tracker")

    @app.route("/purchase-orders",methods=["GET","POST"])
    def purchase_orders():
        if request.method=="POST":
            po=request.form.get("po_number","").strip()
            if po:
                with db() as con:
                    cur=con.execute("INSERT INTO purchase_orders(po_number,supplier_id,job_id,status,order_date,required_date,expected_date,total_value,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                        (po,request.form.get("supplier_id") or None,request.form.get("job_id") or None,request.form.get("status") or "open",request.form.get("order_date") or None,request.form.get("required_date") or None,request.form.get("expected_date") or None,request.form.get("total_value") or None,request.form.get("notes")))
                    rid=cur.lastrowid
                record_event(event_type="PO_MUTATION",action="CREATE",module="purchase_orders",entity_type="purchase_order",entity_id=rid,actor="local")
            return redirect("/purchase-orders")
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="""SELECT p.id,p.po_number,s.name supplier,j.job_number,p.status,p.order_date,p.required_date,p.expected_date,p.total_value
               FROM purchase_orders p LEFT JOIN suppliers s ON s.id=p.supplier_id LEFT JOIN jobs j ON j.id=p.job_id"""; args=()
        if ctype=="job": sql+=" WHERE p.job_id=?"; args=(cid,)
        elif ctype=="supplier": sql+=" WHERE p.supplier_id=?"; args=(cid,)
        elif ctype=="quality_record":
            poid=_linked_id("quality_records",cid,"po_id")
            if poid: sql+=" WHERE p.id=?"; args=(poid,)
        sql+=" ORDER BY p.id DESC LIMIT 300"
        rows=_list(sql,args)
        form="""<details class='panel'><summary><b>Add purchase order</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>PO Number<input name='po_number' required></label><label>Supplier ID<input name='supplier_id' type='number'></label><label>Job ID<input name='job_id' type='number'></label>
<label>Status<input name='status' value='open'></label><label>Order Date<input name='order_date' type='date'></label><label>Required Date<input name='required_date' type='date'></label>
<label>Expected Date<input name='expected_date' type='date'></label><label>Total Value<input name='total_value' type='number' step='.01'></label>
<label class='wide'>Notes<textarea name='notes'></textarea></label><div><button>Save PO</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>Purchasing</p><h1>Purchase Order Tracker</h1><p class='sub'>Due dates, supplier linkage and job impact live in the same context as quality and inventory.</p></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("po_number","PO"),("supplier","Supplier"),("job_number","Job"),("status","Status"),("required_date","Required"),("expected_date","Expected"),("total_value","Value")],"purchase_order","po_number")+"</div>"
        return page("Purchase Order Tracker",body,module_key="purchase_orders")

    @app.route("/inventory",methods=["GET","POST"])
    def inventory():
        if request.method=="POST":
            item=request.form.get("item_number","").strip()
            if item:
                with db() as con:
                    cur=con.execute("INSERT INTO inventory_items(item_number,description,material_spec,location,on_hand,allocated,reorder_point,supplier_id,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                        (item,request.form.get("description"),request.form.get("material_spec"),request.form.get("location"),request.form.get("on_hand") or 0,request.form.get("allocated") or 0,request.form.get("reorder_point") or 0,request.form.get("supplier_id") or None,request.form.get("notes")))
                    rid=cur.lastrowid
                record_event(event_type="INVENTORY_MUTATION",action="CREATE",module="inventory",entity_type="inventory_item",entity_id=rid,actor="local")
            return redirect("/inventory")
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="SELECT id,item_number,description,material_spec,location,on_hand,allocated,(on_hand-allocated) available,reorder_point,status FROM inventory_items"; args=()
        if ctype=="supplier": sql+=" WHERE supplier_id=?"; args=(cid,)
        elif ctype=="job":
            sql="SELECT DISTINCT i.id,i.item_number,i.description,i.material_spec,i.location,i.on_hand,i.allocated,(i.on_hand-i.allocated) available,i.reorder_point,i.status FROM inventory_items i JOIN inventory_transactions t ON t.item_id=i.id WHERE t.job_id=?"; args=(cid,)
        sql+=" ORDER BY id DESC LIMIT 300"
        rows=_list(sql,args)
        form="""<details class='panel'><summary><b>Add inventory item</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Item Number<input name='item_number' required></label><label>Description<input name='description'></label><label>Material Spec<input name='material_spec'></label><label>Location<input name='location'></label>
<label>On Hand<input name='on_hand' type='number' step='.001' value='0'></label><label>Allocated<input name='allocated' type='number' step='.001' value='0'></label>
<label>Reorder Point<input name='reorder_point' type='number' step='.001' value='0'></label><label>Supplier ID<input name='supplier_id' type='number'></label>
<label class='wide'>Notes<textarea name='notes'></textarea></label><div><button>Save Item</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>Materials</p><h1>Inventory Tracker</h1><p class='sub'>On-hand, allocations, job consumption and purchasing risk share the same event stream.</p></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("item_number","Item"),("description","Description"),("material_spec","Spec"),("location","Location"),("on_hand","On Hand"),("allocated","Allocated"),("available","Available"),("reorder_point","Reorder"),("status","Status")],"inventory_item","item_number")+"</div>"
        return page("Inventory Tracker",body,module_key="inventory")

    @app.route("/clocking-errors",methods=["GET","POST"])
    def clocking_errors():
        if request.method=="POST":
            desc=request.form.get("description","").strip()
            if desc:
                with db() as con:
                    cur=con.execute("INSERT INTO clocking_errors(employee_ref,job_id,operation,error_type,reported_by,description) VALUES(?,?,?,?,?,?)",
                        (request.form.get("employee_ref"),request.form.get("job_id") or None,request.form.get("operation"),request.form.get("error_type") or "unknown",request.form.get("reported_by") or "local",desc))
                    rid=cur.lastrowid
                record_event(event_type="CLOCKING_MUTATION",action="CREATE",module="clocking",entity_type="clocking_error",entity_id=rid,actor=request.form.get("reported_by") or "local")
                publish("clocking.error",source_module="clocking",entity_type="clocking_error",entity_id=str(rid),actor=request.form.get("reported_by") or "local",payload={"job_id":request.form.get("job_id"),"error_type":request.form.get("error_type")})
            return redirect("/clocking-errors")
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="""SELECT c.id,c.employee_ref,j.job_number,c.operation,c.error_type,c.reported_by,c.status,c.description,c.created_at
               FROM clocking_errors c LEFT JOIN jobs j ON j.id=c.job_id"""; args=()
        if ctype=="job": sql+=" WHERE c.job_id=?"; args=(cid,)
        sql+=" ORDER BY c.id DESC LIMIT 300"
        rows=_list(sql,args)
        form="""<details class='panel'><summary><b>Report clocking error</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Employee Ref<input name='employee_ref'></label><label>Job ID<input name='job_id' type='number'></label><label>Operation<input name='operation'></label>
<label>Error Type<input name='error_type' placeholder='wrong job, missed punch, bad op...'></label><label>Reported By<input name='reported_by'></label>
<label class='wide'>Description<textarea name='description' required></textarea></label><div><button>Report Error</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>Labor / ERP Data Quality</p><h1>Job Clocking Error Reporting</h1><p class='sub'>Report bad punches and wrong-job/operation clocking without hiding the downstream cost, schedule and quality impact.</p></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("employee_ref","Employee Ref"),("job_number","Job"),("operation","Operation"),("error_type","Error"),("reported_by","Reported By"),("status","Status"),("description","Description"),("created_at","Created")],"clocking_error","error_type")+"</div>"
        return page("Job Clocking Errors",body,module_key="clocking")

    @app.route("/quality",methods=["GET"])
    def quality():
        pulse=quality_pulse(); ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="""SELECT q.id,q.record_number,q.record_type,q.severity,q.status,p.part_number,j.job_number,po.po_number,s.name supplier,q.quantity_affected,q.owner,q.due_date,q.description
               FROM quality_records q LEFT JOIN parts p ON p.id=q.part_id LEFT JOIN jobs j ON j.id=q.job_id LEFT JOIN purchase_orders po ON po.id=q.po_id LEFT JOIN suppliers s ON s.id=q.supplier_id"""; args=()
        field_map={"job":"q.job_id","purchase_order":"q.po_id","part":"q.part_id","supplier":"q.supplier_id","machine":"q.machine_id"}
        if ctype in field_map: sql+=f" WHERE {field_map[ctype]}=?"; args=(cid,)
        elif ctype=="fai":
            qid=_linked_id("fai_runs",cid,"id")
        sql+=" ORDER BY q.id DESC LIMIT 400"
        rows=_list(sql,args)
        ppm=pulse["ppm"]["ppm"]
        cards=f"""<div class='grid'><div class='card'><strong class='big'>{pulse['open_quality']}</strong><span class='label'>Open Records</span></div>
<div class='card'><strong class='big'>{pulse['overdue']}</strong><span class='label'>Overdue</span></div><div class='card'><strong class='big'>{pulse['open_cars']}</strong><span class='label'>Open CARs</span></div>
<div class='card'><strong class='big'>{'n/a' if ppm is None else round(ppm,1)}</strong><span class='label'>30-Day PPM</span></div></div>"""
        body="<section class='page-head'><div class='grow'><p class='eyebrow'>Quality Forge</p><h1>Quality Command Center</h1><p class='sub'>NCR, DMR, RMA, CAR/CAPA, deviations, inspection rejects, supplier quality, PPM, FAI and PPAP evidence all connect back to jobs, POs, inventory, machines, drawings and ERP records.</p></div><a class='button' href='/quality/new'>New Quality Record</a></section>"+context_banner()+cards+"<div class='panel' style='margin-top:14px'>"+table_html(rows,[("record_number","Record"),("record_type","Type"),("severity","Severity"),("status","Status"),("part_number","Part"),("job_number","Job"),("po_number","PO"),("supplier","Supplier"),("quantity_affected","Qty"),("owner","Owner"),("due_date","Due"),("description","Condition")],"quality_record","record_number")+"</div>"
        return page("Quality Forge",body,module_key="quality")

    @app.route("/quality/new",methods=["GET","POST"])
    def quality_new():
        if request.method=="POST":
            data={k:request.form.get(k) for k in request.form}
            for k in ("customer_id","supplier_id","part_id","job_id","po_id","machine_id"):
                data[k]=int(data[k]) if data.get(k) else None
            rid=create_quality_record(data,actor=request.form.get("actor") or "local")
            return redirect(url_for("context_record",entity_type="quality_record",entity_id=rid))
        body="""<section class='page-head'><div><p class='eyebrow'>Controlled occurrence</p><h1>New Quality Record</h1></div></section>
<div class='panel'><form method='post' class='form-grid'>
<label>Type<select name='record_type'><option>NCR</option><option>DMR</option><option>RMA</option><option>CAR</option><option>CAPA</option><option>DEVIATION</option><option>INSPECTION_REJECT</option><option>CUSTOMER_COMPLAINT</option><option>SUPPLIER_NCR</option></select></label>
<label>Record Number<input name='record_number' required></label><label>Severity<input name='severity' value='unassigned'></label><label>Status<input name='status' value='open'></label>
<label>Customer ID<input name='customer_id' type='number'></label><label>Supplier ID<input name='supplier_id' type='number'></label><label>Part ID<input name='part_id' type='number'></label><label>Job ID<input name='job_id' type='number'></label>
<label>PO ID<input name='po_id' type='number'></label><label>Machine ID<input name='machine_id' type='number'></label><label>Qty Affected<input name='quantity_affected' type='number' value='0'></label><label>Qty Shipped<input name='quantity_shipped' type='number' value='0'></label>
<label>Owner<input name='owner'></label><label>Due Date<input name='due_date' type='date'></label><label>Actor<input name='actor' value='local'></label>
<label class='wide'>Condition / Description<textarea name='description' required></textarea></label><label class='wide'>Immediate Containment<textarea name='containment'></textarea></label>
<div><button>Create + Route</button></div></form></div>"""
        return page("New Quality Record",body,module_key="quality")

    @app.get("/methods")
    def methods():
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="""SELECT p.id,p.job_number,p.part_number,p.revision,p.customer,p.quantity,p.required_date,p.status,
                      COUNT(DISTINCT o.id) operations,COUNT(DISTINCT d.id) dependencies
               FROM ezm_method_plans p
               LEFT JOIN ezm_operations o ON o.plan_id=p.id
               LEFT JOIN ezm_dependencies d ON d.operation_id=o.id"""
        args=()
        if ctype=="job":
            job=_linked_id("jobs",cid,"job_number")
            if job:
                sql+=" WHERE p.job_number=?"; args=(job,)
        elif ctype=="part":
            part=_linked_id("parts",cid,"part_number")
            if part:
                sql+=" WHERE p.part_number=?"; args=(part,)
        sql+=" GROUP BY p.id ORDER BY p.id DESC LIMIT 300"
        rows=_list(sql,args)
        body="<section class='page-head'><div><p class='eyebrow'>Methods / Routing Intelligence</p><h1>EZ Methods</h1><p class='sub'>Routing operations, material/tool/gage/fixture/outside-process dependencies, GD&T characteristics and operation readiness. Dependency status feeds purchasing, inventory, jobs, quality and the audit/event spine.</p></div></section>"+context_banner()+"<div class='panel'>"+table_html(rows,[("job_number","Job"),("part_number","Part"),("revision","Rev"),("customer","Customer"),("quantity","Qty"),("required_date","Required"),("status","Status"),("operations","Ops"),("dependencies","Dependencies")],"method_plan","job_number")+"</div>"
        return page("EZ Methods / Routings",body,module_key="ez_methods")

    @app.route("/pm",methods=["GET","POST"])
    def pm():
        if request.method=="POST":
            with db() as con:
                cur=con.execute("INSERT INTO machines(machine_number,name,department,location,criticality,manufacturer,model,serial_number,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                    tuple(request.form.get(k) for k in ("machine_number","name","department","location","criticality","manufacturer","model","serial_number","notes")))
                rid=cur.lastrowid
            record_event(event_type="PM_MUTATION",action="MACHINE_CREATE",module="pm",entity_type="machine",entity_id=rid,actor="local")
            return redirect("/pm")
        rows=_list("SELECT id,machine_number,name,department,location,criticality,status,manufacturer,model FROM machines ORDER BY id DESC LIMIT 300")
        form="""<details class='panel'><summary><b>Add machine</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Machine Number<input name='machine_number' required></label><label>Name<input name='name' required></label><label>Department<input name='department'></label><label>Location<input name='location'></label>
<label>Criticality<input name='criticality'></label><label>Manufacturer<input name='manufacturer'></label><label>Model<input name='model'></label><label>Serial Number<input name='serial_number'></label>
<label class='wide'>Notes<textarea name='notes'></textarea></label><div><button>Save Machine</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>Maintenance</p><h1>PM / Equipment</h1><p class='sub'>Native PM replaces the standalone tracker while keeping machine/task/completion behavior and connecting failures to jobs, capacity and quality.</p></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("machine_number","Machine"),("name","Name"),("department","Department"),("location","Location"),("criticality","Criticality"),("status","Status"),("manufacturer","Mfr"),("model","Model")],"machine","machine_number")+"</div>"
        return page("PM / Equipment",body,module_key="pm")

    @app.route("/vault",methods=["GET","POST"])
    def vault():
        if request.method=="POST":
            with db() as con:
                cur=con.execute("INSERT INTO documents(document_number,title,revision,document_type,status,part_id,job_id,storage_reference,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                    (request.form.get("document_number"),request.form.get("title"),request.form.get("revision"),request.form.get("document_type") or "drawing",request.form.get("status") or "draft",request.form.get("part_id") or None,request.form.get("job_id") or None,request.form.get("storage_reference"),request.form.get("notes")))
                rid=cur.lastrowid
            record_event(event_type="VAULT_MUTATION",action="DOCUMENT_CREATE",module="vault",entity_type="document",entity_id=rid,actor="local")
            return redirect("/vault")
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="SELECT id,document_number,title,revision,document_type,status,part_id,job_id,storage_reference FROM documents"; args=()
        if ctype=="job": sql+=" WHERE job_id=?"; args=(cid,)
        elif ctype=="part": sql+=" WHERE part_id=?"; args=(cid,)
        sql+=" ORDER BY id DESC LIMIT 300"
        rows=_list(sql,args)
        form="""<details class='panel'><summary><b>Add controlled document</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Document Number<input name='document_number'></label><label>Title<input name='title' required></label><label>Revision<input name='revision'></label><label>Type<input name='document_type' value='drawing'></label>
<label>Status<input name='status' value='draft'></label><label>Part ID<input name='part_id' type='number'></label><label>Job ID<input name='job_id' type='number'></label><label>Storage Reference<input name='storage_reference'></label>
<label class='wide'>Notes<textarea name='notes'></textarea></label><div><button>Save Document</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>ForgeVault</p><h1>Drawing / Document Vault</h1><p class='sub'>Revision-controlled document metadata and release history feed jobs, quoting, FAI and quality.</p></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("document_number","Document"),("title","Title"),("revision","Rev"),("document_type","Type"),("status","Status"),("part_id","Part ID"),("job_id","Job ID"),("storage_reference","Storage")],"document","title")+"</div>"
        return page("Drawing / Document Vault",body,module_key="vault")

    @app.get("/ez-fair")
    def ez_fair():
        ctype,cid=request.args.get("context_type"),request.args.get("context_id")
        sql="""SELECT f.id,f.fai_number,f.status,f.characteristic_count,f.pass_count,f.fail_count,p.part_number,j.job_number,f.drawing_revision,f.ballooned_pdf,f.fai_workbook
               FROM fai_runs f LEFT JOIN parts p ON p.id=f.part_id LEFT JOIN jobs j ON j.id=f.job_id"""; args=()
        if ctype=="job": sql+=" WHERE f.job_id=?"; args=(cid,)
        elif ctype=="part": sql+=" WHERE f.part_id=?"; args=(cid,)
        sql+=" ORDER BY f.id DESC LIMIT 300"
        rows=_list(sql,args)
        body="<section class='page-head'><div><p class='eyebrow'>EZ FAIR</p><h1>FAI / Inspection Planning</h1><p class='sub'>Actual EZ FAIR extraction and FAI workbook logic is vendored into SuperForge. Drawing extraction, ballooning, characteristic review and measurements become auditable records instead of detached files.</p></div></section>"+context_banner()+"<div class='panel'>"+table_html(rows,[("fai_number","FAI"),("status","Status"),("part_number","Part"),("job_number","Job"),("drawing_revision","Rev"),("characteristic_count","Chars"),("pass_count","Pass"),("fail_count","Fail"),("ballooned_pdf","Ballooned"),("fai_workbook","Workbook")],"fai","fai_number")+"</div>"
        return page("EZ FAIR / FAI",body,module_key="ezfair")

    @app.get("/ppap")
    def ppap():
        rows=_list("SELECT id,ppap_number,level,status,owner,submission_date,approval_date,part_id,customer_id FROM ppap_packages ORDER BY id DESC LIMIT 300")
        body="<section class='page-head'><div><p class='eyebrow'>APQP / PPAP</p><h1>PPAP</h1><p class='sub'>Level, evidence, FAI, control records and customer approval stay linked to the same part/revision and quality history.</p></div></section>"+context_banner()+"<div class='panel'>"+table_html(rows,[("ppap_number","PPAP"),("level","Level"),("status","Status"),("owner","Owner"),("part_id","Part ID"),("customer_id","Customer ID"),("submission_date","Submitted"),("approval_date","Approved")],"part","ppap_number")+"</div>"
        return page("PPAP",body,module_key="ppap")

    @app.get("/quoting")
    def quoting():
        rows=_list("SELECT id,quote_number,customer_id,part_id,due_date,status,owner,estimated_value,notes FROM quote_intakes ORDER BY id DESC LIMIT 300")
        body="<section class='page-head'><div><p class='eyebrow'>Estimating</p><h1>Quoting</h1><p class='sub'>Quote intake, drawing context, material risk, supplier lead time, capacity and quality history can all feed the same review.</p></div></section>"+context_banner()+"<div class='panel'>"+table_html(rows,[("quote_number","Quote"),("customer_id","Customer ID"),("part_id","Part ID"),("due_date","Due"),("status","Status"),("owner","Owner"),("estimated_value","Value"),("notes","Notes")],"part","quote_number")+"</div>"
        return page("Quoting",body,module_key="quoting")

    @app.get("/planning")
    def planning():
        rows=_list("SELECT id,workflow_key,step_key,source_module,target_module,entity_type,entity_id,assigned_to,status,due_date,created_at FROM workflow_actions ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END,id DESC LIMIT 500")
        body="<section class='page-head'><div><p class='eyebrow'>Cross-module work</p><h1>Planning / Action Queue</h1><p class='sub'>Derived actions from quality, PM, purchasing, inventory, clocking, jobs and ERP sync land here with source events and target modules attached.</p></div></section>"+context_banner()+"<div class='panel'>"+table_html(rows,[("workflow_key","Workflow"),("step_key","Step"),("source_module","Source"),("target_module","Target"),("entity_type","Entity"),("entity_id","ID"),("assigned_to","Owner"),("status","Status"),("due_date","Due"),("created_at","Created")],"job","workflow_key")+"</div>"
        return page("Planning / Capacity",body,module_key="planning")

    @app.route("/suppliers",methods=["GET","POST"])
    def suppliers():
        if request.method=="POST":
            with db() as con:
                cur=con.execute("INSERT INTO suppliers(name,code,contact,email,phone,notes) VALUES(?,?,?,?,?,?)",tuple(request.form.get(k) for k in ("name","code","contact","email","phone","notes")))
                rid=cur.lastrowid
            record_event(event_type="SUPPLIER_MUTATION",action="CREATE",module="suppliers",entity_type="supplier",entity_id=rid,actor="local")
            return redirect("/suppliers")
        rows=_list("SELECT id,name,code,contact,email,phone,status,notes FROM suppliers ORDER BY name")
        form="""<details class='panel'><summary><b>Add supplier</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Name<input name='name' required></label><label>Code<input name='code'></label><label>Contact<input name='contact'></label><label>Email<input name='email' type='email'></label>
<label>Phone<input name='phone'></label><label class='wide'>Notes<textarea name='notes'></textarea></label><div><button>Save Supplier</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>Supply Chain</p><h1>Supplier History</h1></div></section>"+context_banner()+form+"<div class='panel'>"+table_html(rows,[("name","Supplier"),("code","Code"),("contact","Contact"),("email","Email"),("phone","Phone"),("status","Status"),("notes","Notes")],"supplier","name")+"</div>"
        return page("Supplier History",body,module_key="suppliers")

    @app.route("/integrations",methods=["GET","POST"])
    def integrations():
        if request.method=="POST":
            config={"path":request.form.get("path",""),"outbox":request.form.get("outbox",""),"base_url":request.form.get("base_url","")}
            with db() as con:
                cur=con.execute("INSERT INTO erp_connections(name,erp_type,adapter_type,direction,config_json,credentials_ref) VALUES(?,?,?,?,?,?)",
                    (request.form.get("name"),request.form.get("erp_type") or "generic",request.form.get("adapter_type") or "flatfile",request.form.get("direction") or "bidirectional",json.dumps(config),request.form.get("credentials_ref")))
                rid=cur.lastrowid
            record_event(event_type="INTEGRATION_CONFIG",action="CREATE",module="integrations",entity_type="erp_connection",entity_id=rid,actor="local",data={"name":request.form.get("name"),"adapter":request.form.get("adapter_type")})
            return redirect("/integrations")
        rows=_list("SELECT id,name,erp_type,adapter_type,direction,enabled,credentials_ref,updated_at FROM erp_connections ORDER BY id DESC")
        runs=_list("SELECT id,run_id,direction,entity_type,status,read_count,applied_count,error_count,started_at,completed_at FROM integration_runs ORDER BY id DESC LIMIT 30")
        form="""<details class='panel'><summary><b>Add ERP / system connection</b></summary><form method='post' class='form-grid' style='margin-top:12px'>
<label>Name<input name='name' required placeholder='JobBOSS2 Production'></label><label>ERP Type<input name='erp_type' placeholder='JobBOSS2, Epicor, Plex, SAP, Infor...'></label>
<label>Adapter<select name='adapter_type'><option value='flatfile'>CSV/JSON Report Drop</option><option value='rest'>REST API</option><option value='sql'>Approved SQL/Report View</option></select></label>
<label>Direction<select name='direction'><option>bidirectional</option><option>in</option><option>out</option></select></label>
<label>File / DB Path<input name='path'></label><label>Outbox Path<input name='outbox'></label><label class='wide'>REST Base URL<input name='base_url'></label>
<label class='wide'>Credential Reference<input name='credentials_ref' placeholder='Reference to OS/secret-store credential, never the secret itself'></label><div><button>Save Connection</button></div></form></details>"""
        body="<section class='page-head'><div><p class='eyebrow'>Universal adapter layer</p><h1>ERP / Systems Integration</h1><p class='sub'>Flat files, scheduled report drops, REST APIs, approved report/database views and queued outbound writes use configurable mappings, durable sync IDs, conflict handling and audit receipts. Proprietary ERPs only need an adapter for the interface they expose.</p></div></section>"+context_banner()+form+"<div class='panel'><h2>Connections</h2>"+table_html(rows,[("name","Name"),("erp_type","ERP"),("adapter_type","Adapter"),("direction","Direction"),("enabled","Enabled"),("credentials_ref","Credential Ref"),("updated_at","Updated")],"erp_connection","name")+"</div><div class='panel'><h2>Recent sync runs</h2>"+table_html(runs,[("run_id","Run"),("direction","Direction"),("entity_type","Entity"),("status","Status"),("read_count","Read"),("applied_count","Applied"),("error_count","Errors"),("started_at","Started"),("completed_at","Done")],"integration_run","run_id")+"</div>"
        return page("ERP / Systems",body,module_key="integrations")

    @app.get("/intelligence")
    def intelligence():
        pats=patterns()
        proposals=_list("SELECT id,proposal_id,title,target_module,risk_level,status,execution_permission,reviewed_by,updated_at FROM learning_proposals ORDER BY id DESC LIMIT 100")
        observed="".join(f"<tr><td>{e(x['signal_key'])}</td><td>{x['count']}</td><td>{e(x['average_human_rating'])}</td><td>{e(x['latest_outcome'])}</td></tr>" for x in pats) or "<tr><td colspan='4' class='empty'>Not enough repeated observations yet.</td></tr>"
        body="<section class='page-head'><div><p class='eyebrow'>BEAN inside SuperForge</p><h1>Intelligence / Learning</h1><p class='sub'>BEAN can remember outcomes, detect repeating patterns and propose better routing, thresholds or controls. Production logic remains deterministic; proposed changes require recorded review and permission.</p></div></section>"+context_banner()+f"<div class='panel'><h2>Learned patterns</h2><table><tr><th>Signal</th><th>Count</th><th>Human Rating</th><th>Latest Outcome</th></tr>{observed}</table></div><div class='panel'><h2>Improvement proposals</h2>"+table_html(proposals,[("proposal_id","Proposal"),("title","Title"),("target_module","Module"),("risk_level","Risk"),("status","Status"),("execution_permission","Permission"),("reviewed_by","Reviewed By"),("updated_at","Updated")],"learning_proposal","title")+"</div>"
        return page("BEAN Intelligence",body,module_key="bean")

    @app.get("/logic")
    def logic():
        rows=logic_matrix()
        body="<section class='page-head'><div><p class='eyebrow'>System nervous system</p><h1>Cross-Module Logic Map</h1><p class='sub'>These are deterministic event relationships. Every derived action retains its source event and correlation ID.</p></div></section><div class='panel'><table><tr><th>Source</th><th>Event</th><th>Targets</th></tr>"+"".join(f"<tr><td><b>{e(r['source'])}</b></td><td>{e(r['event'])}</td><td>{e(r['targets'])}</td></tr>" for r in rows)+"</table></div>"
        return page("Logic Map",body)

    @app.get("/audit")
    def audit():
        verify=verify_journal()
        entries=list(reversed(tail_entries(250)))
        rows=[{"id":r.get("sequence"),"time":r.get("timestamp_utc"),"event":r.get("event_type"),"action":r.get("action"),"module":r.get("module"),"entity":f"{r.get('entity_type','')} {r.get('entity_id','')}","actor":r.get("actor"),"correlation":r.get("correlation_id"),"hash":str(r.get("entry_hash",""))[:12]} for r in entries]
        body=f"<section class='page-head'><div><p class='eyebrow'>Immutable evidence spine</p><h1>Audit Trail</h1><p class='sub'>Append-only JSONL with sequence numbers, before/after hashes, event IDs, correlation IDs and a SHA-256 hash chain. Application uninstall does not target the ProgramData audit directory.</p></div><span class='badge accent'>{'VERIFIED' if verify['ok'] else 'FAILED'}</span></section><div class='panel'><div class='statline'><span>Entries: <b>{verify.get('entries')}</b></span><span>Last hash: <code>{e(str(verify.get('last_hash',''))[:24])}</code></span><span>Path: <code>{e(verify.get('path'))}</code></span></div></div><div class='panel'>"+table_html(rows,[("id","Seq"),("time","Time UTC"),("event","Event"),("action","Action"),("module","Module"),("entity","Entity"),("actor","Actor"),("correlation","Correlation"),("hash","Hash")],"audit_event","event")+"</div>"
        return page("Audit Trail",body,module_key="audit")

    @app.route("/appearance",methods=["GET","POST"])
    def appearance():
        if request.method=="POST":
            mode=request.form.get("theme_mode") if request.form.get("theme_mode") in {"dark","light"} else "dark"
            accent=request.form.get("accent") or "#1F6FBC"
            if not (accent.startswith("#") and len(accent) in {4,7}): accent="#1F6FBC"
            with db() as con:
                con.execute("""INSERT INTO user_preferences(user_key,theme_mode,accent,compact_mode) VALUES('local',?,?,0)
                               ON CONFLICT(user_key) DO UPDATE SET theme_mode=excluded.theme_mode,accent=excluded.accent,updated_at=CURRENT_TIMESTAMP""",(mode,accent))
            record_event(event_type="UI_PREFERENCE",action="UPDATE",module="shell",entity_type="user_preferences",entity_id="local",actor="local",data={"theme_mode":mode,"accent":accent})
            return redirect("/appearance")
        body="""<section class='page-head'><div><p class='eyebrow'>Keep it simple</p><h1>Appearance</h1><p class='sub'>Dark stays the default. Accent changes affect buttons, active navigation and subtle highlights. Light mode changes the neutral surfaces without spraying the accent across the whole UI.</p></div></section>
<div class='panel'><form method='post' class='form-grid'><label>Mode<select name='theme_mode'><option value='dark'>Dark</option><option value='light'>Light</option></select></label>
<label>Accent Color<input name='accent' type='color' value='#1F6FBC'></label><div><button>Save Appearance</button></div></form></div>"""
        return page("Appearance",body)

    @app.get("/api/context-menu")
    def api_context_menu():
        return jsonify({"items":menu_for(request.args.get("entity_type",""),request.args.get("entity_id",""),request.args.get("current_module",""))})

    @app.get("/context/<entity_type>/<entity_id>")
    def context_record(entity_type,entity_id):
        table_map={"job":"jobs","purchase_order":"purchase_orders","inventory_item":"inventory_items","clocking_error":"clocking_errors","quality_record":"quality_records","machine":"machines","document":"documents","supplier":"suppliers","fai":"fai_runs","erp_connection":"erp_connections","integration_run":"integration_runs","learning_proposal":"learning_proposals","method_plan":"ezm_method_plans"}
        table=table_map.get(entity_type)
        if not table:
            return page("Record",f"<div class='panel'>Unknown entity type: {e(entity_type)}</div>",context_type=entity_type,context_id=entity_id),404
        with db() as con:
            row=con.execute(f"SELECT * FROM {table} WHERE id=?",(entity_id,)).fetchone()
        if not row:
            return page("Record","<div class='panel'>Record not found.</div>",context_type=entity_type,context_id=entity_id),404
        d=dict(row)
        details="<table>"+"".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k,v in d.items())+"</table>"
        body=f"<section class='page-head'><div><p class='eyebrow'>{e(entity_type)}</p><h1>{e(next((d.get(k) for k in ('record_number','job_number','po_number','item_number','machine_number','fai_number','name','title') if d.get(k)),entity_id))}</h1><p class='sub'>Right-click this page or any linked tracker to carry this record into another module.</p></div></section><div class='panel sf-context' data-entity-type='{e(entity_type)}' data-entity-id='{e(entity_id)}' data-entity-label='{e(entity_type)} {e(entity_id)}'>{details}</div>"
        return page("Record Detail",body,context_type=entity_type,context_id=entity_id)

    @app.get("/health")
    def health():
        return jsonify({"ok":True,"app":"SuperForge","schema":"1.0.0-unified","audit":verify_journal()})

    return app
