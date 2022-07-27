# Copyright (c) 2022, BizMap and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
import json

class RoomFolioHMS(Document):
	pass
	
	
@frappe.whitelist()	
def map_sign_in_sheet_with_room_folio(source_name, target_doc=None):
    target_doc = get_mapped_doc("Room Folio HMS", source_name,
       {
        "Room Folio HMS": {
            "doctype": "Sign In Sheet HMS",
            "field_map": {
                "name": "folio",
                
              
            },
        }
           }, target_doc)
      
    return target_doc
    
@frappe.whitelist()    	
def description_for_sales_books(name):
    decs= frappe.db.sql(f"""
    SELECT description from `tabSales Order Item` where parent='{name}'
 """, as_dict=1)
    return decs    	
    
    
    
@frappe.whitelist()    
def room_folio_sales_invoice(source_name, target_doc=None):    
    target_doc = get_mapped_doc("Room Folio HMS", source_name,
       {
        "Room Folio HMS": {
            "doctype": "Sales Invoice",
            "field_map": {
                "name": "room_folio_ref",
                "customer":"customer"
                
              
            },
        }
           }, target_doc)
      
    return target_doc

   
@frappe.whitelist()    
def sales_order_item_transfer_to_sales_invoice(room_folio_ref):
    sales_order_child_itm=[]
    if room_folio_ref:
       sales_order_ref =[i.sales_order for i in frappe.db.sql(f"""select sales_order from `tabSales Book Item` where parent='{room_folio_ref}' """,as_dict=1)]
       #print(sales_order_ref)
       for i in sales_order_ref:
           sales_order_itm=frappe.db.sql(f"""select a.item_code,a.uom,a.description,a.item_name,m.total_qty,a.conversion_factor,a.item_tax_template, m.total from `tabSales Order` as m inner join `tabSales Order Item` as a on a.parent=m.name  where m.name="{i}" """,as_dict=0)
           sales_order_child_itm.append(sales_order_itm)
    return sales_order_child_itm     
    
    
    
    
    
    
