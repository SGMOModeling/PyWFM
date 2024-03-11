.. _misc:

#################
IWFMMiscellaneous
#################

.. currentmodule:: pywfm.misc.IWFMMiscellaneous

API Version
===========

.. autosummary::
   :toctree: generated/version/

   get_version

Time-Related
============

.. autosummary::
   :toctree: generated/time/

   get_n_intervals
   increment_time
   is_date_greater

Logging Messages
================

.. autosummary::
   :toctree: generated/logging/

   get_last_message
   log_last_message
   set_log_file
   close_log_file

IWFM-Internal
=============

.. autosummary::
   :toctree: generated/internal/

   get_flow_destination_type_id
   get_flow_destination_type_id_element
   get_flow_destination_type_id_elementset
   get_flow_destination_type_id_gwelement
   get_flow_destination_type_id_lake
   get_flow_destination_type_id_outside
   get_flow_destination_type_id_streamnode
   get_flow_destination_type_id_subregion
   get_land_use_type_id_gen_ag
   get_land_use_type_id_native_riparian
   get_land_use_type_id_nonponded_ag
   get_land_use_type_id_refuge
   get_land_use_type_id_rice
   get_land_use_type_id_urban
   get_land_use_type_id_urban_indoor
   get_land_use_type_id_urban_outdoor
   get_land_use_type_ids
   get_land_use_type_ids_1
   get_location_type_id_bypass
   get_location_type_id_diversion
   get_location_type_id_element
   get_location_type_id_gwheadobs
   get_location_type_id_lake
   get_location_type_id_node
   get_location_type_id_smallwatershed
   get_location_type_id_streamhydobs
   get_location_type_id_streamnode
   get_location_type_id_streamnodebud
   get_location_type_id_streamreach
   get_location_type_id_subregion
   get_location_type_id_subsidenceobs
   get_location_type_id_tiledrainobs
   get_location_type_id_zone
   get_location_type_ids
   get_location_type_ids_1
   get_supply_type_id_diversion
   get_supply_type_id_elempump
   get_supply_type_id_well
   get_zbudget_type_ids
   get_zone_extent_id_horizontal
   get_zone_extent_id_vertical
   get_zone_extent_ids
   get_budget_type_ids
   get_data_unit_type_id_area
   get_data_unit_type_id_length
   get_data_unit_type_ids
   get_data_unit_type_volume

Private Methods
===============

.. autosummary::
   :toctree: generated/private/

   _is_time_interval_greater_or_equal
   _string_to_list_by_array
   _validate_iwfm_date
   _validate_time_interval