from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _order_outstanding_statement_dict(self, data: dict):
        converted_data = []
        currencies_amounts = {}

        partner_ids = data.keys()
        for partner_id in partner_ids:
            for key, value in data[partner_id]['currencies'].items():
                currency_name = self.env['res.currency'].browse(key).name

                converted_data.append({
                    'name': self.browse(partner_id).name,
                    'date': data[partner_id]['today'],
                    'currency_id': currency_name,
                    'amount': value['amount_due']
                })
                if not currencies_amounts.get(currency_name, False):
                    currencies_amounts[currency_name] = value['amount_due']
                else:
                    currencies_amounts[currency_name] += value['amount_due']

        return converted_data, currencies_amounts
