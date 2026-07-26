// Copyright (c) 2026, Innosphere Consulting LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("FCM Revenue Sales Upload", {
	refresh(frm) {
		if (!frm.doc.__islocal && !frm.doc.sales_invoice_reference) {
			frm.add_custom_button(__("Process & Generate Invoice"), () => {
				frappe.call({
					method: "food_court_management.fcm.billing.process_revenue_share",
					args: { revenue_upload_name: frm.doc.name },
					freeze: true,
					callback: (r) => {
						frappe.msgprint(__("Sales Invoice created: {0}", [r.message.sales_invoice || "N/A"]));
						frm.reload_doc();
					},
				});
			}).addClass("btn-primary");
		}
	},
});
