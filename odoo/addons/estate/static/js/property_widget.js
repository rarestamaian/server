odoo.define('user_property_lazyload.PropertyWidget', function (require) {
    "use strict";

    const AbstractField = require('web.AbstractField');
    const registry = require('web.field_registry');
    const core = require('web.core');
    const qweb = core.qweb;

    const PropertyWidget = AbstractField.extend({
        template: 'PropertyWidgetTemplate',
        events: {
            'click .load-more': '_onLoadMore',
        },
        init: function () {
            this._super.apply(this, arguments);
            this.properties = [];
            this.offset = 0;
            this.limit = 50;
        },
        start: function () {
            this._loadProperties();
        },
        _loadProperties: function () {
            const self = this;
            this._rpc({
                route: '/user/properties',
                params: {
                    user_id: this.recordData.id,
                    offset: this.offset,
                    limit: this.limit,
                },
            }).then(function (result) {
                self.properties = self.properties.concat(result);
                self.offset += self.limit;
                self._render();
            });
        },
        _render: function () {
            this.$('.property-list').html(qweb.render('PropertyListTemplate', { properties: this.properties }));
        },
        _onLoadMore: function () {
            this._loadProperties();
        },
    });

    registry.add('property_widget', PropertyWidget);

    return PropertyWidget;
});
