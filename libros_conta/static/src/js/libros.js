/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LibrosController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    }

    async onClickImprimir() {
        const state = this.model.root;
        const domain = state.domain;
        const resModel = state.resModel;
        
        const fields = Object.keys(state.activeFields).filter(
            fieldName => {
                const field = state.fields[fieldName];
                return field && field.exportable !== false;
            }
        );

        try {
            const result = await this.orm.call(
                resModel,
                "imprimir",
                [null, fields, domain, this.props.context || {}],
                { context: this.props.context }
            );
            
            if (result) {
                await this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add(
                "Error al generar el reporte",
                { type: "danger" }
            );
            console.error("Error al imprimir:", error);
        }
    }
}

// ✅ NO asignar template aquí - la herencia XML funciona automáticamente

export const librosListView = {
    ...listView,
    Controller: LibrosController,
};

registry.category("views").add("libros_list_view", librosListView);