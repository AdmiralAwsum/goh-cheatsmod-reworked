(include "/properties/resupply.inc")

(define "cheat_supply_ammo"
	("supply_ammo" supply(0))
	{extender "supply_zone"
		{fuel 	{amount 5}	{value 1}}
		{resupply
			("items_explosives")
			("items_engineer")
			("items_medic")
		}
		{radius				30}
		{resupplyPeriod		3}
		{regenerationPeriod 0}
		{limit				0}
	}
)

(define "cheat_supply_ammo_global"
	("supply_ammo" supply(0))
	{extender "supply_zone"
		{fuel 	{amount 10}	{value 1}}
		{resupply
			("items_medic")
		}
		{radius				500}
		{resupplyPeriod		5}
		{regenerationPeriod 0}
		{limit				0}
	}
)
