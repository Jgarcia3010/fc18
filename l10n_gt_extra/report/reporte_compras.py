# -*- encoding: utf-8 -*-

from odoo import api, models
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ReporteCompras(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_compras'

    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['num_normal'] = 0
        totales['num_fesp'] = 0
        totales['num_peq'] = 0
        totales['num_nc'] = 0
        totales['num_nd'] = 0
        totales['num_na'] = 0
        totales['num_fcam'] = 0
        totales['num_fcex'] = 0

        # factura nota_credito nota_debito nota_abono factura_cambiaria factura_cambiaria_exportacion
        totales['compra']       = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0, 'idp': 0}
        totales['servicio']     = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['importacion']  = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['combustible']  = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['compras']      = {'bienes': 0}
        totales['total']        = 0
        totales['resumen']      = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['pequenio_contribuyente'] = 0

        journal_ids = [x for x in datos['diarios_id']]
        # show all purchase taxes
        facturas = self.env['account.move'].search([
            ('state', 'in', ['posted']), # draft invoices should not appear on report
            ('journal_id', 'in', journal_ids),
            ('date', '<=', datos['fecha_hasta']),
            ('date', '>=', datos['fecha_desde']),
            # ('type', '=', 'in_invoice'),
        ], order='date, payment_reference')

        lineas = []
        # iterate through all facturas
        for f in facturas:
            if f.caja_chica:
                # agregar las facturas en f.facturasexternas
                cch_invoices = []
                for le in f.invoice_line_ids:
                    if le.product_id.exclude_libros or not le.facturaexterna:
                        continue
                    precio = (le.price_unit * (1-(le.discount or 0.0)/100.0))
                    r = le.tax_ids._origin.compute_all(precio, currency=f.currency_id, quantity=le.quantity, product=le.product_id, partner=f.partner_id)
                    line_iva_amount = 0
                    line_other_amount = 0
                    for i in r['taxes']:
                        tax_id = self.env['account.tax'].search([('id', '=', i['id'])])
                        if tax_id.sat_tax_type == 'service_good' or not tax_id.sat_tax_type:
                            line_iva_amount += i['amount']
                        elif tax_id.sat_tax_type == 'gas':
                            line_other_amount += i['amount']
                            totales['compra']['idp'] += i['amount']
                    if le.facturaexterna and le.facturaexterna.name not in cch_invoices:
                        if le.facturaexterna.serie and len(le.facturaexterna.serie.split("*")) == 2 and le.facturaexterna.serie.split('*')[1] == 'REMOVE':
                            continue
                        tipo = 'FACT'
                        _logger.info('***********************************')
                        _logger.info('LE: %s', le)
                        _logger.info('FE: %s', le.facturaexterna)
                        fp = (
                            le.facturaexterna.fiscal_position_id.name
                            or le.facturaexterna.proveedor.property_account_position_id.name
                        )
                        is_st = False
                        if fp and 'peque' in fp.lower():
                            tipo += ' PEQ'
                            is_st = True
                        linea = {
                                'estado': f.state,
                                'tipo': tipo,
                                'fecha': le.facturaexterna.fecha,
                                'serie': le.facturaexterna.serie or '',
                                'numero': le.facturaexterna.factura or '',
                                'proveedor': le.facturaexterna.proveedor.name,
                                'nit': le.facturaexterna.proveedor.vat,
                                'compra': le.price_subtotal if (le.product_id.x_studio_bien_o_servicio == 'articulo' and not is_st) else 0,
                                'compra_exento': le.price_subtotal if (le.product_id.x_studio_bien_o_servicio == 'articulo' and is_st) else 0,
                                'servicio': le.price_subtotal if (le.product_id.x_studio_bien_o_servicio == 'servicio' and not is_st) else 0,
                                'servicio_exento': le.price_subtotal if (le.product_id.x_studio_bien_o_servicio == 'servicio' and is_st) else 0,
                                'combustible': le.price_subtotal if (le.product_id.x_studio_bien_o_servicio == 'combustible' and not is_st) else 0,
                                'combustible_exento': le.price_subtotal if (le.product_id.x_studio_bien_o_servicio == 'combustible' and is_st) else 0,
                                'importacion': 0,
                                'importacion_exento': 0,
                                'importacion_iva': 0,
                                'compra_iva': le.price_total-le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'articulo' else 0,
                                'servicio_iva': le.price_total-le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'servicio' else 0,
                                'combustible_iva': le.price_total-le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'combustible' else 0,
                                'base': 0,
                                'iva': line_iva_amount,
                                'idp': line_other_amount,
                                'subtotal_exento': 0, 
                                'total': le.price_total,
                                'origen': f.name
                            }
                        cch_invoices.append(le.facturaexterna.name)
                        lineas.append(linea)
                        totales['num_facturas'] += 1
                    else:
                        for element in lineas:
                            if element['serie'] == le.facturaexterna.serie and element['numero'] == le.facturaexterna.factura:
                                element['compra'] += le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'articulo' else 0
                                element['servicio'] += le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'servicio' else 0
                                element['combustible'] += le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'combustible' else 0

                                element['compra_iva'] += le.price_total-le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'articulo' else 0
                                element['servicio_iva'] += le.price_total-le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'servicio' else 0
                                element['combustible_iva'] += le.price_total-le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'combustible' else 0

                                element['iva'] += line_iva_amount
                                element['idp'] += line_other_amount
                                element['total'] += le.price_total
                    
                    totales['total'] += le.price_total

                    totales['compra']['neto'] += le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'articulo' else 0 
                    totales['compra']['iva'] += line_iva_amount if le.product_id.x_studio_bien_o_servicio == 'articulo' else 0
                    totales['servicio']['neto'] += le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'servicio' else 0
                    totales['servicio']['iva'] += line_iva_amount if le.product_id.x_studio_bien_o_servicio == 'servicio' else 0
                    totales['combustible']['neto'] += le.price_subtotal if le.product_id.x_studio_bien_o_servicio == 'combustible' else 0
                    totales['combustible']['iva'] += line_iva_amount if le.product_id.x_studio_bien_o_servicio == 'combustible' else 0
                    #totales['resumen']['neto'] += le.price_subtotal
                    #totales['resumen']['iva'] += le.price_total
                continue
            if f.journal_id.is_receipt_journal:
                continue

            if f.provider_invoice_serial and len(f.provider_invoice_serial.split("*")) == 2 and f.provider_invoice_serial.split('*')[1] == 'REMOVE':
                continue

            # Verifica si la factura no tiene impuestos
            has_taxes = False
            for line in f.invoice_line_ids:
                if len(line.tax_ids) > 0:
                    has_taxes = True

            #if has_taxes is False:
            #    continue

            # made it here means it has taxes and is not receipt journal
            proveedor = f.partner_id.name
            nit = f.partner_id.vat
            numero = f.provider_invoice_number

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                tipo_cambio = 7.65
                currency_rate_query = self.env['res.currency.rate'].search([], order='name desc', limit=1)
                for rate in currency_rate_query:
                    tipo_cambio = rate.rate
            _logger.info(tipo_cambio)
            tipo = 'FACT'
            if f.type_invoice == 'normal':
                tipo = 'FACT'
                totales['num_normal'] += 1
            elif f.type_invoice == 'nota_debito':
                tipo = 'ND'
                totales['num_nd'] += 1
            elif f.type_invoice == 'especial':
                tipo = 'FESP'
                totales['num_fesp'] += 1
            elif f.type_invoice == 'cambiaria':
                tipo = 'FCAM'
                totales['num_fcam'] += 1
            elif f.type_invoice == 'cambiaria_exp':
                tipo = 'FEXP'
                totales['num_fcex'] += 1

            if f.move_type != 'in_invoice':
                tipo = 'NC'
                totales['num_nc'] += 1

            if f.tax_withholding_isr == 'small_taxpayer_withholding':
                tipo = tipo + ' PEQ'
                totales['num_peq'] += 1

            linea = {
                
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.invoice_date,
                'serie': f.provider_invoice_serial or '',
                # 'numero': f.reference or '',
                'numero': f.provider_invoice_number or '',
                'proveedor': proveedor,
                'nit': nit,
                'compra': 0,
                'compra_exento': 0,
                'servicio': 0,
                'servicio_exento': 0,
                'combustible': 0,
                'combustible_exento': 0,
                'importacion': 0,
                'importacion_exento': 0,
                'importacion_iva': 0,
                'compra_iva': 0,
                'servicio_iva': 0,
                'combustible_iva': 0,
                'base': 0,
                'iva': 0,
                'idp': 0,
                'subtotal_exento': 0, 
                'total': 0,
                'origen': f.name
            }
            is_compra = False
            is_service = False
            is_mix = False
            is_import = False
            is_gas = False
            flag_gas = False
            signo = 1
            add_invoice = False
            for linea_factura in f.invoice_line_ids:
                precio = (linea_factura.price_unit * (1-(linea_factura.discount or 0.0)/100.0)) / tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1
                    signo = -1
                tipo_linea = f.tipo_gasto

                if linea_factura.tax_ids:
                    for tax in linea_factura.tax_ids:
                        if tax.sat_tax_type == 'gas':
                            if is_compra or is_service:
                                is_mix = True
                                flag_gas = True
                            else:
                                is_gas = True
                                flag_gas = True
                    if flag_gas:
                        flag_gas = False

                # garbage code if linea_factura.tax_ids:
                # garbage code     for tax in linea_factura.tax_ids:
                # garbage code         if tax.sat_tax_type == 'gas':
                # garbage code             if is_compra or is_service:
                # garbage code                 is_mix = True
                # garbage code                 flag_gas = True
                # garbage code             else:
                # garbage code                 is_gas = True
                # garbage code                 flag_gas = True
                # garbage code     if flag_gas:
                # garbage code         flag_gas = False

                tipo_linea = linea_factura.product_id.x_studio_bien_o_servicio
                if tipo_linea:
                    if tipo_linea == 'articulo':
                        tipo_linea = 'compra'
                    elif tipo_linea == 'servicio':
                        tipo_linea = 'servicio'
                    elif tipo_linea == 'combustible':
                        tipo_linea = 'combustible'
                else:
                    tipo_linea = 'compra'

                r = linea_factura.tax_ids._origin.compute_all(precio, currency=f.currency_id, quantity=linea_factura.quantity, product=linea_factura.product_id, partner=f.partner_id)

                base_price = (linea_factura.price_subtotal * signo) / tipo_cambio
                linea['base'] += base_price if not linea_factura.product_id.exclude_libros else 0
                totales[tipo_linea]['total'] += base_price

                # totales[tipo_linea]['total'] += precio * linea_factura.quantity

                purchase_taxes_obj = self.env['account.tax'].search([
                    ('type_tax_use', '=', 'purchase')
                ])
                purchase_taxes = []
                for t in purchase_taxes_obj:
                    purchase_taxes.append(t.id)
                    

                if len(linea_factura.tax_ids) > 0:
                    add_invoice = True
                    linea[tipo_linea] += base_price
                    if tipo_linea == 'compra':
                        totales['compras']['bienes'] += base_price
                    totales[tipo_linea]['neto'] += base_price
                    totales['resumen']['neto'] += base_price
                    # r todos los impuestos que tiene la linea de la factura
                    for i in r['taxes']: #cambiar impuesto_id con combustible
                        # si el impuesto es el que seleccione, es el principal
                        if i['id'] == datos['impuesto_id'][0]:
                            linea['iva'] += i['amount']
                            linea[tipo_linea+'_iva'] += i['amount']
                            totales[tipo_linea]['iva'] += i['amount']
                            totales['resumen']['iva'] += base_price
                            totales[tipo_linea]['total'] += i['amount']
                        elif i['amount'] > 0:
                            if tipo_linea == 'combustible' :
                                #linea['compra_exento'] += i['amount']
                                linea['subtotal_exento'] += i['amount']
                                linea[tipo_linea+'_exento'] += i['amount']
                                totales[tipo_linea]['exento'] += i['amount'] 
                                totales[tipo_linea]['total'] += i['amount']
                                linea['idp'] += i['amount']
                                totales['compra']['idp'] += i['amount'] / tipo_cambio
                            else:
                                linea[tipo_linea+'_exento'] += i['amount']
                                totales[tipo_linea]['exento'] += i['amount']
                                totales[tipo_linea]['total'] += i['amount']
                                totales['compra']['iva'] += i['amount']
                            totales['resumen']['exento'] += i['amount']
                elif linea_factura.product_id.exclude_libros:
                    add_invoice = False if not add_invoice else True
                    continue
                else:
                    add_invoice = True
                    linea['subtotal_exento'] += base_price
                    linea[tipo_linea+'_exento'] += base_price
                    totales[tipo_linea]['exento'] += base_price
                    totales['resumen']['exento'] += base_price
                    totales[tipo_linea]['total'] += base_price
                #Se cambio la cantidad * el precio de los impuestos que no estan incluidos
                linea['total'] += (linea_factura.price_total * signo) / tipo_cambio

                totales['total'] += linea_factura.price_total * signo / tipo_cambio

            totales['num_facturas'] += 1 if add_invoice else 0
            print('PC----------', f.partner_id.pequenio_contribuyente)
            if f.partner_id.pequenio_contribuyente:
                totales['pequenio_contribuyente'] += linea['base']
            # if linea['total'] > 0:
            if add_invoice:
                lineas.append(linea)

        return {'lineas': lineas, 'totales': totales}

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        diario = self.env['account.journal'].browse(data['form']['diarios_id'][0])
        
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'direccion': diario.direccion and diario.direccion.street,
            'company_id': self.env.company
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
