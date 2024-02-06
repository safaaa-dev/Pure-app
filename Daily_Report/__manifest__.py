# Copyright 2013 Nicolas Bessi (Camptocamp SA)
# Copyright 2014 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2015 Grupo ESOC (<http://www.grupoesoc.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Daily Report ",
    "summary": "Daily Report",
    "version": "16.0.1.0.1",
    "author": "safaa eltahir ",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "depends": ["base"],
    'data': [
    'security/ir.model.access.csv',
    'views/city_menu.xml',
    'views/city_view.xml',
    'views/neighborhood_view.xml',
    'views/neighborhood_menu.xml',
],
    "auto_install": False,
    "installable": True,
}
