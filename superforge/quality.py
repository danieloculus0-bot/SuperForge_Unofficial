from __future__ import annotations

QUALITY_CAPABILITIES = {
    "nonconformance": ["NCR","DMR","inspection reject","scrap","rework","containment"],
    "corrective_action": ["CAR","CAPA","5-Why","root cause","effectiveness verification"],
    "customer_quality": ["RMA","customer complaint","8D linkage","financial recovery"],
    "supplier_quality": ["supplier NCR","SCAR","incoming inspection","supplier PPM","supplier scorecard"],
    "inspection": ["FAI","EZ FAIR","in-process inspection","final inspection","inspection plan","gage/tool traceability"],
    "ppap_apqp": ["PPAP Level 1-5","PSW","dimensional results","material/performance results","process flow","PFMEA","control plan","MSA","capability"],
    "deviation": ["deviation request","temporary approval","risk review","expiration","customer approval"],
    "metrics": ["PPM","FPY","COPQ","RMA cost","NCR trend","CAR aging","supplier quality","customer quality"],
    "evidence": ["attachments","photos","drawing revision","material cert","inspection record","email/reference","vault release"],
    "audit": ["before/after snapshot","actor","timestamp","reason","correlation id","hash-chain journal"],
}

QUALITY_LINKS = (
    "customer","supplier","part","revision","work_order","operation","purchase_order",
    "inventory_lot","material_heat","machine","employee_reference","drawing","FAI","PPAP","RMA","NCR","CAR"
)
