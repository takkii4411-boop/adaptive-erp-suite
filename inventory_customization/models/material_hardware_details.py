from odoo import models, fields
import xlsxwriter
from io import BytesIO
import base64
from datetime import datetime


class MaterialHardwareDetails(models.Model):
    _name = 'material.hardware.details'
    _description = 'Material & Hardware Details'
    _rec_name = 'estimation_id'

    estimation_id = fields.Many2one(
        'sale.estimation',
        string="Estimation",
        required=True,
        ondelete='cascade'
    )
    project_id = fields.Many2one('project.project', related='estimation_id.project_id', store=True, readonly=True)

    line_ids = fields.One2many(
        'material.hardware.details.line',
        'hardware_id',
        string="Material & Hardware Lines"
    )
    sub_contractor_bom_line_ids = fields.One2many(
        'bom.wizard.subcontractor.line',
        'hardware_id',
        string="Sub-Contractors Lines"
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)

    def action_save_and_close(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window_close',
        }

    def action_export_to_excel(self):
        self.ensure_one()
        import xlsxwriter
        from io import BytesIO
        import base64
        from datetime import datetime

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Material & Hardware')

        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#D3D3D3'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': '#FFFFFF', 'border': 1})
        text_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})

        worksheet.merge_range('A1:O1', f'Material & Hardware Details - {self.estimation_id.name or ""}', title_format)
        worksheet.merge_range('A2:O2',
                              f'Project: {self.project_id.name or ""} | Date: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
                              workbook.add_format({'italic': True}))

        headers = ['No.', 'Sort', 'Category', 'Product', 'Code', 'Color', 'Finish', 'Supplier', 'Sub-Con', 'Arch Code',
                   'UOM', 'Rate', 'Qty', 'Sub Total', 'Margin (%)', 'Comments']
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)

        row = 4
        for idx, line in enumerate(self.line_ids.sorted('sort_no'), 1):
            worksheet.write(row, 0, idx, center_format)
            worksheet.write(row, 1, line.sort_no or '', center_format)
            worksheet.write(row, 2, line.categ_id.display_name or '', text_format)
            worksheet.write(row, 3, line.product_id.display_name or '', text_format)
            worksheet.write(row, 4, line.product_id.default_code or '', text_format)
            worksheet.write(row, 5, line.product_color_id.name or '', text_format)
            worksheet.write(row, 6, line.product_finish_id.name or '', text_format)
            worksheet.write(row, 7, line.supplier_id.name or '', text_format)
            worksheet.write(row, 8, line.sub_con or '', text_format)
            worksheet.write(row, 9, line.arch_code or '', text_format)
            worksheet.write(row, 10, line.uom_id.name or '', text_format)
            worksheet.write(row, 11, line.rate or 0.0, money_format)
            worksheet.write(row, 12, line.qty or 0.0, money_format)
            worksheet.write(row, 13, line.sub_total or 0.0, money_format)
            worksheet.write(row, 14, line.margin or 0.0, money_format)
            worksheet.write(row, 15, line.comments or '', text_format)
            row += 1

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 8)
        worksheet.set_column('C:D', 20)
        worksheet.set_column('E:F', 12)
        worksheet.set_column('G:H', 15)
        worksheet.set_column('I:J', 12)
        worksheet.set_column('K:O', 15)
        worksheet.set_column('P:P', 30)

        sheet2 = workbook.add_worksheet('Sub-Contractors')

        sub_headers = [
            'No.',
            'Category',
            'Sub-Contractor',
            'Description',
            'UOM',
            'Rate',
            'Qty',
            'Margin (%)',
            'Margin Diff (%)',
            'Total Margin (%)',
            'Sub Total',
        ]

        # Title
        sheet2.merge_range('A1:K1', f'Sub-Contractors Details - {self.estimation_id.name or ""}', title_format)

        # Headers in row 2
        for col, header in enumerate(sub_headers):
            sheet2.write(2, col, header, header_format)

        row = 3

        for idx, line in enumerate(self.sub_contractor_bom_line_ids, 1):
            sheet2.write(row, 0, idx, center_format)
            sheet2.write(row, 1, line.product_id.display_name or '', text_format)
            sheet2.write(row, 2, line.subcontractor.name or '', text_format)
            sheet2.write(row, 3, line.description or '', text_format)
            sheet2.write(row, 4, line.uom.name or '', text_format)
            sheet2.write(row, 5, line.rate or 0.0, money_format)
            sheet2.write(row, 6, line.quantity or 0.0, money_format)
            sheet2.write(row, 7, line.margin or 0.0, money_format)
            sheet2.write(row, 8, line.margin_diff or 0.0, money_format)
            sheet2.write(row, 9, line.margin_all or 0.0, money_format)
            sheet2.write(row, 10, line.subtotal or 0.0, money_format)

            row += 1

        # Column widths
        sheet2.set_column('A:A', 5)
        sheet2.set_column('B:B', 22)
        sheet2.set_column('C:C', 20)
        sheet2.set_column('D:D', 30)
        sheet2.set_column('E:E', 10)
        sheet2.set_column('F:K', 15)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': f'Material_Hardware_{self.estimation_id.name or "Details"}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
            'public': True,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=ir.attachment&id={attachment.id}&filename_field=name&field=datas&download=true',
            'target': 'self',
        }

class MaterialHardwareDetailsLine(models.Model):
    _name = 'material.hardware.details.line'
    _description = 'Material & Hardware Detail Line'
    _order = 'sort_no ASC'

    hardware_id = fields.Many2one('material.hardware.details', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Material / Hardware")
    categ_id = fields.Many2one('product.category', string='Category')
    sort_no = fields.Integer(string='Sort No')
    product_code = fields.Char(string='Product Code')
    product_color_id = fields.Many2one('product.color', string='Product Color')
    product_finish_id = fields.Many2one('product.finish', string='Product Finish')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    sub_con = fields.Char('Sub-Con')
    arch_code = fields.Char('Arch Code')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    rate = fields.Float('Rate')
    qty = fields.Float('Qty')
    sub_total = fields.Float('Sub-Total')
    margin = fields.Float('Margin')
    comments = fields.Text('Comments')
    currency_id = fields.Many2one('res.currency', related="hardware_id.currency_id", store=True)
