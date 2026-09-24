from __future__ import annotations
from urllib.parse import urlencode

MODULES=[
 ("job_tracker","Job Tracker","/jobs"),
 ("purchase_orders","Purchase Order Tracker","/purchase-orders"),
 ("inventory","Inventory Tracker","/inventory"),
 ("clocking","Job Clocking Errors","/clocking-errors"),
 ("quality","Quality Forge","/quality"),
 ("pm","PM / Equipment","/pm"),\n ("ez_methods","EZ Methods / Routings","/methods"),
 ("vault","Drawing / Document Vault","/vault"),
 ("ezfair","EZ FAIR / FAI","/ez-fair"),
 ("ppap","PPAP","/ppap"),
 ("quoting","Quoting","/quoting"),
 ("planning","Planning / Capacity","/planning"),
 ("suppliers","Supplier History","/suppliers"),
 ("integrations","ERP / Systems","/integrations"),
 ("bean","BEAN Intelligence","/intelligence"),
 ("audit","Audit Trail","/audit"),
]
ENTITY_RELEVANCE={
 "job":{"job_tracker","purchase_orders","inventory","clocking","quality","pm","ez_methods","vault","ezfair","ppap","planning","integrations","bean","audit"},
 "purchase_order":{"purchase_orders","job_tracker","inventory","quality","suppliers","integrations","bean","audit"},
 "inventory_item":{"inventory","purchase_orders","job_tracker","quality","suppliers","quoting","integrations","bean","audit"},
 "clocking_error":{"clocking","job_tracker","quality","bean","audit"},
 "quality_record":{"quality","job_tracker","purchase_orders","inventory","pm","ez_methods","vault","ezfair","ppap","suppliers","bean","audit"},
 "machine":{"pm","job_tracker","quality","planning","bean","audit"},
 "document":{"vault","ezfair","quality","job_tracker","quoting","integrations","audit"},
 "part":{"job_tracker","quality","ez_methods","vault","ezfair","ppap","inventory","quoting","suppliers","bean","audit"},
 "supplier":{"suppliers","purchase_orders","inventory","quality","quoting","bean","audit"},
 "fai":{"ezfair","ez_methods","quality","job_tracker","vault","ppap","bean","audit"},\n "method_plan":{"ez_methods","job_tracker","purchase_orders","inventory","quality","pm","vault","ezfair","planning","bean","audit"},
}
def menu_for(entity_type:str="",entity_id:str="",current_module:str="")->list[dict]:
    allowed=ENTITY_RELEVANCE.get(entity_type,{key for key,_,_ in MODULES})
    query=urlencode({"context_type":entity_type,"context_id":entity_id}) if entity_type and entity_id else ""
    rows=[]
    for key,label,path in MODULES:
        if key not in allowed: continue
        rows.append({"key":key,"label":label,"href":path+(("?"+query) if query else ""),"current":key==current_module})
    return rows
