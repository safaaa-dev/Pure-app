# Copyright 2013 Nicolas Bessi (Camptocamp SA)
# Copyright 2014 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2015 Grupo ESOC (<http://www.grupoesoc.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "City District",
    "summary": "City District",
    "version": "16.0.1.0.1",
    "author": "safaa eltahir "
    "Grupo ESOC Ingeniería de Servicios, "
    "Tecnativa, "
    "LasLabs, "
    "ACSONE SA/NV, "
    "DynApps NV, "
    "Odoo Community Association (OCA)",
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
