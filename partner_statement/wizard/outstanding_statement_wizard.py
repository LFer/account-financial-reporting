# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class OutstandingStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _name = "outstanding.statement.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Wizard"

    def _prepare_statement(self):
        res = super()._prepare_statement()
        res.update(
            {
                "is_outstanding": True,
            }
        )

        if self.initial_date:
            res.update({"initial_date": self.initial_date})
            
        if self.env.context.get("from_menu"):
            res["partner_ids"] = self._get_partners_with_open_items_at_date()

        return res

    def _get_partners_with_open_items_at_date(self):
        """Use the statement cutoff, including items reconciled after that date."""
        self.ensure_one()
        excluded_account_ids = self._get_excluded_accounts().ids
        self.env.cr.execute(
            """
            SELECT DISTINCT line.partner_id
              FROM account_move_line line
              JOIN account_move move ON move.id = line.move_id
              JOIN account_account account ON account.id = line.account_id
             WHERE line.partner_id IS NOT NULL
               AND line.company_id = %(company_id)s
               AND line.date <= %(date_end)s
               AND move.state = 'posted'
               AND account.account_type = %(account_type)s
               AND (%(date_start)s IS NULL OR move.invoice_date >= %(date_start)s)
               AND (NOT %(show_only_overdue)s OR COALESCE(line.date_maturity, line.date) <= %(date_end)s)
               AND (NOT %(excluded_accounts)s OR line.account_id NOT IN %(excluded_account_ids)s)
               AND (
                   %(sent_to_dgi_filter)s = 'all'
                   OR (%(sent_to_dgi_filter)s = 'only_electronic' AND move.cfe_emitido IS TRUE)
                   OR (%(sent_to_dgi_filter)s = 'only_manual' AND move.cfe_emitido IS NOT TRUE)
               )
               AND (
                   line.amount_residual != 0
                   OR line.amount_residual_currency != 0
                   OR EXISTS (
                       SELECT 1
                         FROM account_partial_reconcile partial
                        WHERE (partial.debit_move_id = line.id OR partial.credit_move_id = line.id)
                          AND partial.max_date > %(date_end)s
                   )
               )
             ORDER BY line.partner_id
            """,
            {
                "company_id": self.company_id.id,
                "date_end": self.date_end,
                "account_type": self.account_type,
                "date_start": self.initial_date or None,
                "show_only_overdue": self.show_only_overdue,
                "excluded_accounts": bool(excluded_account_ids),
                "excluded_account_ids": tuple(excluded_account_ids) or (-1,),
                "sent_to_dgi_filter": self.sent_to_dgi_filter,
            },
        )
        return [partner_id for (partner_id,) in self.env.cr.fetchall()]

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_statement()
        if report_type == "xlsx":
            report_name = "p_s.report_outstanding_statement_xlsx"
        else:
            report_name = "partner_statement.outstanding_statement"

        self = self.with_context(hide_detailed=self.hide_detailed)

        consumidor_final_id = self.env.ref('l10n_uy_einvoice_base.consumidor_final_partner_id', raise_if_not_found=False)
        if consumidor_final_id and data["partner_ids"] != [consumidor_final_id.id]:
            if consumidor_final_id.id in data['partner_ids']:
                data['partner_ids'].remove(consumidor_final_id.id)

        partners = self.env["res.partner"].browse(data["partner_ids"])
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(partners, data=data)
        )

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)
