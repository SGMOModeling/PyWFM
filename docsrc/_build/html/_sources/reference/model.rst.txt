.. _model:

##########
IWFMModel
##########

.. currentmodule:: pywfm.IWFMModel

Time-Related
============

.. autosummary::
   :toctree: generated/time/

   get_current_date_and_time
   get_n_time_steps
   get_time_specs
   get_n_intervals
   get_output_interval
   is_date_greater
   increment_time

Model Geometry
==============

Nodes
-----

.. autosummary::
   :toctree: generated/geometry/nodes/

   get_n_nodes
   get_node_coordinates
   get_node_ids
   get_node_info
   get_boundary_nodes
   order_boundary_nodes
   
Elements
--------

.. autosummary::
   :toctree: generated/geometry/elements/

   get_n_elements
   get_element_config
   get_element_ids
   get_element_info
   get_element_spatial_info
   
Subregions
----------

.. autosummary::
   :toctree: generated/geometry/subregions/
   
   get_n_subregions
   get_subregion_ids
   get_subregion_name
   get_subregion_names
   get_subregions_by_element
   
Stratigraphy
------------

.. autosummary::
   :toctree: generated/geometry/stratigraphy/
   
   get_n_layers
   get_ground_surface_elevation
   get_aquifer_top_elevation
   get_aquifer_bottom_elevation
   get_stratigraphy_atXYcoordinate
   
Lakes
-----

.. autosummary::
   :toctree: generated/geometry/lakes/
   
   get_n_lakes
   get_lake_ids
   get_n_elements_in_lake
   get_elements_in_lake
   
Streams
-------

.. autosummary::
   :toctree: generated/geometry/streams/
   
   get_n_stream_reaches
   get_stream_reach_ids
   get_stream_reach_names
   get_n_nodes_in_stream_reach
   get_stream_reach_stream_nodes
   get_stream_reach_groundwater_nodes
   get_n_stream_nodes
   get_stream_node_ids
   get_stream_bottom_elevations
   get_n_rating_table_points
   get_stream_rating_table
   get_n_stream_nodes_upstream_of_stream_node
   get_stream_nodes_upstream_of_stream_node
   get_upstream_nodes_in_stream_reaches
   get_downstream_node_in_stream_reaches
   get_reach_outflow_destination
   get_reach_outflow_destination_types
   get_n_reaches_upstream_of_reach
   get_reaches_upstream_of_reach
   is_stream_upstream_node
   get_stream_network

Inflows and Small Watersheds
============================

.. autosummary::
   :toctree: generated/inflows/

   get_n_stream_inflows
   get_stream_inflow_ids
   get_stream_inflow_nodes
   get_n_small_watersheds
   get_small_watershed_ids
   
Tile Drains
===========

.. autosummary::
   :toctree: generated/drains/
   
   get_n_tile_drains
   get_tile_drain_ids
   get_tile_drain_nodes
   
Land Use
========

.. autosummary::
   :toctree: generated/landuse/
   
   get_n_ag_crops

   
Streams and Bypasses
====================

.. autosummary::
   :toctree: generated/streams/

   get_stream_flow_at_location
   get_stream_flows
   get_stream_gain_from_groundwater
   get_stream_gain_from_lakes
   get_stream_inflows_at_some_locations
   get_stream_rainfall_runoff
   get_stream_reaches_for_stream_nodes
   get_stream_return_flows
   get_stream_riparian_evapotranspiration
   get_stream_stages
   get_stream_tile_drain_flows
   get_stream_tributary_inflows
   get_net_bypass_inflows
   get_actual_stream_diversions_at_some_locations
   

Diversions and Pumping
======================

.. autosummary::
   :toctree: generated/diversions/

   get_n_diversions
   get_diversion_ids
   get_diversion_purpose
   get_stream_diversion_locations
   get_n_wells
   get_well_ids
   get_well_pumping_purpose
   get_n_element_pumps
   get_element_pump_ids
   get_element_pump_purpose
   get_urban_diversion_supply_shortage_at_origin
   get_urban_elempump_supply_shortage_at_origin
   get_urban_well_supply_shortage_at_origin
   get_ag_diversion_supply_shortage_at_origin
   get_ag_elempump_supply_shortage_at_origin
   get_ag_well_supply_shortage_at_origin
   get_supply_requirement_ag_elements
   get_supply_requirement_ag_subregions
   get_supply_requirement_urban_elements
   get_supply_requirement_urban_subregions

Aquifer Properties
==================

.. autosummary::
   :toctree: generated/aquiferprops

   get_aquifer_horizontal_k
   get_aquifer_vertical_k
   get_aquitard_vertical_k
   get_aquifer_specific_storage
   get_aquifer_specific_yield
   get_aquifer_parameters

Simulation Results 
==================

.. autosummary::
   :toctree: generated/heads/

   get_gwheads_foralayer
   get_depth_to_water
   get_gwheads_all
   get_subsidence_all
   get_subregion_ag_pumping_average_depth_to_water
   get_zone_ag_pumping_average_depth_to_water


Simulation Hydrographs
======================

.. autosummary::
   :toctree: generated/hydrographs/

   get_n_subsidence_hydrographs
   get_subsidence_hydrograph_ids
   get_subsidence_hydrograph_coordinates
   get_subsidence_hydrograph_names
   get_subsidence_hydrograph
   get_n_tile_drain_hydrographs
   get_tile_drain_hydrograph_ids
   get_tile_drain_hydrograph_coordinates  
   get_n_groundwater_hydrographs
   get_groundwater_hydrograph_ids
   get_groundwater_hydrograph_coordinates
   get_groundwater_hydrograph_names
   get_groundwater_hydrograph_info
   get_groundwater_hydrograph
   get_groundwater_hydrograph_at_node_and_layer
   get_n_stream_hydrographs
   get_stream_hydrograph_ids
   get_stream_hydrograph_coordinates
   get_stream_hydrograph_names
   get_stream_hydrograph
   get_n_hydrograph_types
   get_hydrograph_type_list

Plotting
========

.. autosummary::
   :toctree: generated/plotting
   
   plot_nodes
   plot_elements
  



Model Simulation
================

.. autosummary::
   :toctree: generated/simulation/

   advance_state
   advance_time
   read_timeseries_data
   read_timeseries_data_overwrite
   restore_pumping_to_read_values
   set_log_file
   close_log_file
   get_last_message
   log_last_message
   set_preprocessor_path
   set_simulation_path
   turn_supply_adjustment_on_off
   set_supply_adjustment_max_iterations
   set_supply_adjustment_tolerance
   simulate_all
   simulate_for_an_interval
   simulate_for_one_timestep
   print_results
   is_end_of_simulation

General
=======

.. autosummary::
   :toctree: generated/general/

   kill
   is_model_instantiated
   delete_inquiry_data_file
   get_version

Private Methods
===============

.. autosummary::
   :toctree: generated/private/

   _is_time_interval_greater_or_equal
   _get_names
   _get_n_hydrographs
   _get_hydrograph_ids
   _get_hydrograph_coordinates
   _get_hydrograph
   _string_to_list_by_array
   _validate_iwfm_date
   _validate_time_interval
   _get_supply_purpose
   _get_supply_requirement_ag
   _get_supply_requirement_urban
   _get_supply_shortage_at_origin_ag
   _get_supply_shortage_at_origin_urban
   _get_n_locations
   _get_location_ids

IWFM-Internal
=============

.. autosummary::
   :toctree: generated/internal/

   get_data_unit_type_id_area
   get_data_unit_type_id_length
   get_data_unit_type_ids
   get_data_unit_type_volume
   get_flow_destination_type_id
   get_flow_destination_type_id_element
   get_flow_destination_type_id_elementset
   get_flow_destination_type_id_gwelement
   get_flow_destination_type_id_lake
   get_flow_destination_type_id_outside
   get_flow_destination_type_id_streamnode
   get_flow_destination_type_id_subregion
   get_land_use_ids
   get_land_use_type_id_gen_ag
   get_land_use_type_id_native_riparian
   get_land_use_type_id_nonponded_ag
   get_land_use_type_id_refuge
   get_land_use_type_id_rice
   get_land_use_type_id_urban
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
   get_supply_type_id_diversion
   get_supply_type_id_elempump
   get_supply_type_id_well
   get_zone_extent_id_horizontal
   get_zone_extent_id_vertical
   get_zone_extent_ids
   get_budget_type_ids
   get_zbudget_type_ids

