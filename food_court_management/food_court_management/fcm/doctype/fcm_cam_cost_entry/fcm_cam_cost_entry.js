// Copyright (c) 2026, Innosphere Consulting LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("FCM CAM Cost Entry", {
	refresh(frm) {
		if (frm.doc.status === "Pending Allocation" && frm.doc.food_court && frm.doc.month && frm.doc.year) {
			frm.add_custom_button(__("Run CAM Allocation & Billing"), () => {
				frappe.call({
					method: "food_court_management.fcm.api.billing_api.run_cam_allocation",
					args: {
						food_court: frm.doc.food_court,
						month: frm.doc.month,
						year: frm.doc.year,
					},
					freeze: true,
					freeze_message: __("Allocating CAM cost and generating invoices..."),
					callback: (r) => {
						frappe.msgprint(__("CAM allocation completed. Invoices created: {0}", [r.message.invoices_created.length]));
						frm.reload_doc();
					},
				});
			}).addClass("btn-primary");
		}
	},
});
