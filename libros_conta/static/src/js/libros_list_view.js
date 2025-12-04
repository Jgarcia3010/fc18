/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { ListRenderer } from "@web/views/list/list_renderer";

/**
 * Controlador personalizado para listas del módulo Libros
 */
class LibrosListController extends ListController {
    setup() {
        super.setup();
        // Aquí puedes agregar cualquier lógica extra
        // por ejemplo logs:
        console.log("LibrosListController cargado correctamente");
    }
}

/**
 * Renderer personalizado (opcional)
 */
class LibrosListRenderer extends ListRenderer {
    setup() {
        super.setup();
        // Aquí podrías personalizar el render
        // Ejemplo:
        console.log("LibrosListRenderer activo");
    }
}

/**
 * Registramos una nueva vista basada en listView,
 * con nuestros componentes personalizados.
 */
const librosListView = {
    ...listView,
    Controller: LibrosListController,
    Renderer: LibrosListRenderer,
};

registry.category("views").add("libros_list_view", librosListView);

console.log("Vista personalizada 'libros_list_view' registrada correctamente.");
