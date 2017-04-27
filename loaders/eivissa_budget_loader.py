# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class EivissaBudgetLoader(SimpleBudgetLoader):

    # An artifact of the in2csv conversion of the original XLS files is a trailing '.0', which we remove here
    def clean(self, s):
        return s.split('.')[0]

    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        programme_mapping = {
            # old programme: new programme
            # '1340': '1350',     # Protección Civil
            '1350': '1360',     # Extinción de incendios
            '1500': '1510',     # Política territorial
            '1720': '1700',     # Medio ambiente
            '2300': '2310',     # Servicios sociales
            '2330': '2315',     # Discapacitats
            # '1550': '1532',     # Vías públicas
            # '1620': '1621',     # Recogida de residuos
            # '3130': '3110',     # Protección de la salud
            '3210': '3230',     # Educación
            # '3220': '3229',     # Enseñanza secundaria
            # '3230': '3239',     # Promoción educativa
            '3242': '3260',     # Educación vial
            # '3340': '3341',     # Promoción cultural
            # '4410': '4411',     # Promoción, mantenimiento y desarrollo del transporte
            # '4940': '4911',     # URBAN- Arona 2007-2013
        }

        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)
        if is_expense:
            # We sometimes miss the leading zero, so add it back if needed
            fc_code = self.clean(line[1]).rjust(4, '0')
            ec_code = self.clean(line[2])

            # For years before 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)
            if int(year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)

            return {
                'is_expense': True,
                'is_actual': is_actual,
                'fc_code': fc_code,
                'ec_code': ec_code[:3],         # First three digits
                'ic_code': '000',
                'item_number': ec_code[3:],     # Everything beyond third digits
                'description': line[3],
                'amount': self._parse_amount(line[10 if is_actual else 7])
            }

        else:
            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': line[2][:3],         # First three digits
                'ic_code': '000',               # All income goes to the root node
                'item_number': line[2][3:],     # Fourth and fifth digit; careful, there's trailing dirt
                'description': line[3],
                'amount': self._parse_amount(line[9 if is_actual else 4])
            }
