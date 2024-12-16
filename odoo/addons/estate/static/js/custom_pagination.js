// odoo.define('estate.custom_pagination', function (require) {
//     "use strict";
    
//     var ListView = require('web.ListView');
//     var rpc = require('web.rpc');

//     ListView.include({
//         _onPaginationChange: function (ev) {
//             this._super(ev);
//             // Fetch the total number of records
//             this._updateRecordCount();
//         },

//         _updateRecordCount: function () {
//             // var self = this;
//             rpc.query({
//                 model: 'estate.property',
//                 method: 'get_total_estate_count',
//                 args: [],
//             }).then(function (total_count) {
//                 // Update the existing element with the total count
//                 const pagerLimitElement = document.querySelector('span.o_pager_limit');
//                 if (pagerLimitElement) {
//                     pagerLimitElement.textContent = total_count;
//                 } else {
//                     console.error("Element 'span.o_pager_limit' not found.");
//                 }
//             }).catch(function (error) {
//                 console.error("Error fetching total record count", error);
//             });
//         }
//     });
// });
