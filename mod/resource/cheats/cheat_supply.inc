(include "/properties/resupply.inc")

(define "cheat_supply_ammo"
	{extender "supply_zone"
		{fuel 	{amount 5}	{value 1}}
		{resupply
			("items_light_generic")
			("items_light_ger")
			("items_light_rus")
			("items_light_eng")
			("items_light_usa")
			("items_light_fin")
			("items_light_jap")
			("items_light_fra")
			("items_heavy_generic")
			("items_heavy_ger")
			("items_heavy_rus")
			("items_heavy_eng")
			("items_heavy_fin")
			("items_heavy_usa")
			("items_heavy_jap")
			("items_heavy_fra")
			("items_explosives")
			("items_engineer")
			("items_medic")
		}
		{radius				30}
		{resupplyPeriod		3}
		{regenerationPeriod 0}
		{limit				0}
	}
	{DecalView supply_zone
		{Sprite "supply_zone.ebm"
			{Visibility 0.25}
		}
		{Layer grounddynamic}
		{Visible 0}
	}
)

(define "cheat_supply_ammo_global"
	{extender "supply_zone"
		{fuel 	{amount 10}	{value 1}}
		{resupply
			("items_light_generic")
			("items_light_ger")
			("items_light_rus")
			("items_light_eng")
			("items_light_usa")
			("items_light_fin")
			("items_light_jap")
			("items_light_fra")
			("items_heavy_generic")
			("items_heavy_ger")
			("items_heavy_rus")
			("items_heavy_eng")
			("items_heavy_fin")
			("items_heavy_usa")
			("items_heavy_jap")
			("items_heavy_fra")
			("items_medic")
		}
		{radius				500}
		{resupplyPeriod		5}
		{regenerationPeriod 0}
		{limit				0}
	}
)
