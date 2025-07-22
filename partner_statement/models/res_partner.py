from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _order_outstanding_statement_dict(self, data: dict):
        converted_data = []
        currencies_amounts = {}

        partner_ids = data.keys()
        for partner_id in partner_ids:
            for key, value in data[partner_id]['currencies'].items():
                amount_rounded = round(value['amount_due'], 2)
                currency_name = self.env['res.currency'].browse(key).name

                converted_data.append({
                    'name': self.browse(partner_id).name,
                    'date': data[partner_id]['today'],
                    'currency_id': currency_name,
                    'amount': amount_rounded
                })
                if key not in currencies_amounts:
                    currencies_amounts[currency_name] = amount_rounded
                else:
                    currencies_amounts[currency_name] += amount_rounded

        return converted_data, currencies_amounts
