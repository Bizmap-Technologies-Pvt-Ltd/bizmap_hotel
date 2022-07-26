# -*- coding: utf-8 -*-
# Copyright (c) 2020, bizmap technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime ,timedelta
import calendar
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from frappe.model.mapper import get_mapped_doc
import json
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc



#after selecting check in date and intering number of night it calcuulate check out date Autometically on Sales Order
@frappe.whitelist()
def check_out_date(doc):
    doc=json.loads(doc)
    if doc.get('no_of_nights_cf') and doc.get('check_in_cf'):
       check_in=str(doc.get('check_in_cf'))
       checkIn_strp=datetime. strptime(check_in,"%Y-%m-%d")
       checkInformate=datetime(checkIn_strp.year,checkIn_strp.month,checkIn_strp.day)
       checkOutdate = checkInformate + relativedelta(days=(int(doc.get('no_of_nights_cf'))))
       return checkOutdate.date()

#inserting item table on sale order
@frappe.whitelist()
def insert_items(doc):
    doc=json.loads(doc)
    if doc.get("no_of_nights_cf") and doc.get('number_of_room'):
       room_pakage=doc.get('room_package_cf')
       no_of_night= float(doc.get('no_of_nights_cf')) * doc.get('number_of_room') 
       check_in_date=doc.get('check_in_cf')
       check_out_date = doc.get('check_out_cf')
       room_package_description=frappe.db.get_value('Item',{'name':doc.get('room_package_cf')},['description','stock_uom'])
       return room_pakage,no_of_night,check_in_date,check_out_date,room_package_description
#mapping info from sales order to room folio
@frappe.whitelist()
def doc_mapped_to_room_folia(source_name, target_doc=None):
    #print(doc.name)
    target_doc = get_mapped_doc("Sales Order", source_name,
       {
        "Sales Order": {
            "doctype": "Room Folio HMS",
            "field_map": {  
                "name": "reservation",
                "customer":"customer",
                "guest_cf":"guest",
                "reservation_notes_cf":"reservation_notes",
                "room_type_cf":"room_type",
                "room_no_cf":"room_no",
                "property":"property",
                "room_package_cf":"room_package",
                "check_out_cf":"check_out",
                "no_of_nights_cf":"quantity",
                "room_rate_cf":"room_rate",
                "contact_mobile":"customer_mobile",
                "contact_email": "customer_email"
              
            },
        }
           }, target_doc)
      
    return target_doc
#creating multiple room folio on after entering number of room more then 1
@frappe.whitelist()
def doc_mapped_to_for_multiple_room_folio(doc):
    doc =json.loads(doc)
    existing_room_folio=frappe.db.get_value("Room Folio HMS",{'reservation':doc.get('name')},'name')
    if not existing_room_folio:
       for i in range(doc.get('number_of_room')):
           New_room_folio = frappe.new_doc('Room Folio HMS')
           New_room_folio.reservation = doc.get('name')
           New_room_folio.customer = doc.get('customer')
           New_room_folio.reservation_notes= doc.get('reservation_notes_cf')
           New_room_folio.room_type = doc.get('room_type_cf')
           New_room_folio.room_package = doc.get('room_package_cf')
           New_room_folio.room_rate = doc.get('room_rate_cf')
           New_room_folio.check_out=doc.get('check_out_cf')
           if doc.get("weekend_rate_cf"):
              New_room_folio.room_rate=doc.get("weekend_rate_cf")
           
           New_room_folio.insert(
            ignore_permissions=True,
            ignore_links=True,
            ignore_if_duplicate=True,
            ignore_mandatory=True
            )
           New_room_folio.run_method('submit')

#it's check Avaliblity of room on booking date if room is not avalible on paticular booking date it will throw msg
def before_submit(doc,method):
       
    #check_room_avablity
    occupied_room_room_folio=[i.m for i in frappe.db.sql(f""" select COUNT(room_type)as m from `tabRoom Folio HMS` where check_out BETWEEN "{doc.check_in_cf}" AND "{doc.check_out_cf}" AND room_type='{doc.room_type_cf}'  And status="Checked Out" """, as_dict=1)]
    print("occupied_room",occupied_room_room_folio)
    total_room=[i.m for i in frappe.db.sql(f""" select COUNT(room_type) as m from `tabRoom HMS` where room_type="{doc.room_type_cf}" and  status!="Out Of Order"  """, as_dict=1)]
    print("total_room",total_room)
    occupied_booking_room_from_so=[0 if i.m  is None else i.m for i in frappe.db.sql(f""" select  SUM(number_of_room) as m from `tabSales Order`
where room_type_cf="{doc.room_type_cf}" And docstatus!=2 and check_in_cf  between "{doc.check_in_cf}" and "{doc.check_out_cf}" or room_type_cf="{doc.room_type_cf}" And docstatus!=2 and check_out_cf between "{doc.check_in_cf}" and "{doc.check_out_cf}" or check_out_cf > "{doc.check_out_cf}" and room_type_cf="{doc.room_type_cf}" And docstatus!=2 """, as_dict=1)]
  
    if occupied_booking_room_from_so[0]<=total_room[0]:
        avalible_room = total_room[0]- occupied_booking_room_from_so[0]
        print("occupied_booking_room_from_so+++++++++++",occupied_booking_room_from_so)
        update_room_type=frappe.get_doc("Room Type HMS",doc.room_type_cf)
        update_room_type.total_room=total_room[0]
        update_room_type.available_room_= avalible_room
        update_room_type.save()

    else:
         frappe.throw(f"Booking In Room Type {doc.room_type_cf} for date {doc.check_in_cf} is alrady full.Please try for different Date or Room Type")
        
         
#getting contact details of guest and filling in sales order doctype            
@frappe.whitelist()	       
def get_name_mobile_emalil_frm_contact(doc):
    doc = json.loads(doc)
    contact_details={}
    if doc.get("guest_cf"):
       get_phone=[contact_details.update({"phone":i.phone}) for i in frappe.db.sql(f""" select phone from `tabContact Phone` where parent="{doc.get("guest_cf")}" """,as_dict=1)]
       get_email= [contact_details.update({"email_id":i.email_id}) for i in frappe.db.sql(f""" select email_id from `tabContact Email` where parent="{doc.get("guest_cf")}" """,as_dict=1)]
       contact_details.update({"name":frappe.db.get_value("Contact",{"name":doc.get("guest_cf")},"name")})
       contact_full_name=frappe.db.get_value("Contact",{"name":doc.get("guest_cf")},["first_name","last_name"])
       contact_details.update({"full_name":' '.join(i for i in contact_full_name if i is not None)})
       return contact_details

 
 
