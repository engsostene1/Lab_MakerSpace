# this file  exposes the four menu functions
#that is main.py can do:
#from menus import members_menu, equipment_menu, loans_menu, reports_menu
from menus.members_menu   import members_menu
from menus.equipment_menu import equipment_menu
from menus.loans_menu     import loans_menu
from menus.reports_menu   import reports_menu

__all__ = ["members_menu", "equipment_menu", "loans_menu", "reports_menu"]