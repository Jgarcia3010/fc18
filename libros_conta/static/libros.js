odoo.define('libros_conta.LibrosController ', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var qweb = core.qweb;

    var LibrosController = ListController.extend({

        // -------------------------------------------------------------------------
        // Public
        // -------------------------------------------------------------------------

        init: function (parent, model, renderer, params) {
            this.context = renderer.state.getContext();
            return this._super.apply(this, arguments);
        },

        /**
        * @override
        */
        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            var $button = $(qweb.render('LibrosConta.BotonImprimir'));
            $button.click(function () {
                let state = self.model.get(self.handle);
                const domain = state.getDomain();
                let fields = self.renderer.columns.filter(field => field.tag === 'field' && state.fields[field.attrs.name].exportable !== false).map(field => field.attrs.name);

                self._rpc({
                    model: state.model,
                    method: "imprimir",
                    args: [null, fields, domain, self.odoo_context || {} ],
                    context: self.odoo_context,
                }).then(function(result){
                    if (!result) return;
                        
                    var nextAction = self.do_action(result);
                    $button.attr('disabled', false);
                    return nextAction;
                }).guardedCatch(function() {
                    $button.attr('disabled', false);
                });;
            });
            this.$buttons.prepend($button);
        },
    });


    var LibrosView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: LibrosController
        })
    });

    viewRegistry.add('libros_list_view', LibrosView);

});
