import ctypes
import datetime
import numpy as np


class IWFMMiscellaneous:
    """IWFM Miscellaneous Class for interacting with the IWFM API

    Returns
    -------
    IWFMMiscellaneous Object
        instance of the IWFMMiscellaneous class and access to the IWFM
        Miscellaneous fortran procedures.

    Note
    ----
    This class is a base class and is not meant to be called directly.
    It is not provided with an __init__ method, so the self.dll used in
    each of the methods must be provided through the subclass.
    """

    def get_data_unit_type_id_length(self):
        if not hasattr(self.dll, "IW_GetDataUnitTypeID_Length"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetDataUnitTypeID_Length")
            )

        # initialize output variables
        length_unit_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetDataUnitTypeID_Length(
            ctypes.byref(length_unit_id), ctypes.byref(status)
        )

        return length_unit_id.value

    def get_data_unit_type_id_area(self):
        if not hasattr(self.dll, "IW_GetDataUnitTypeID_Area"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetDataUnitTypeID_Area")
            )

        # initialize output variables
        area_unit_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetDataUnitTypeID_Area(
            ctypes.byref(area_unit_id), ctypes.byref(status)
        )

        return area_unit_id.value

    def get_data_unit_type_volume(self):
        if not hasattr(self.dll, "IW_GetDataUnitTypeID_Volume"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetDataUnitTypeID_Volume")
            )

        # initialize output variables
        volume_unit_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetDataUnitTypeID_Volume(
            ctypes.byref(volume_unit_id), ctypes.byref(status)
        )

        return volume_unit_id.value

    def get_data_unit_type_ids(self):
        if not hasattr(self.dll, "IW_GetDataUnitTypeIDs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetDataUnitTypeIDs")
            )

        # initialize output variables
        length_unit_id = ctypes.c_int(0)
        area_unit_id = ctypes.c_int(0)
        volume_unit_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetDataUnitTypeIDs(
            ctypes.byref(length_unit_id),
            ctypes.byref(area_unit_id),
            ctypes.byref(volume_unit_id),
            ctypes.byref(status),
        )

        return dict(
            length=length_unit_id.value,
            area=area_unit_id.value,
            volume=volume_unit_id.value,
        )

    def get_land_use_type_id_gen_ag(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeID_GenAg"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeID_GenAg")
            )

        # initialize output variables
        gen_ag_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeID_GenAg(
            ctypes.byref(gen_ag_landuse_id), ctypes.byref(status)
        )

        return gen_ag_landuse_id.value

    def get_land_use_type_id_urban(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeID_Urban"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeID_Urban")
            )

        # initialize output variables
        urban_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeID_Urban(
            ctypes.byref(urban_landuse_id), ctypes.byref(status)
        )

        return urban_landuse_id.value

    def get_land_use_type_id_nonponded_ag(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeID_NonPondedAg"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeID_NonPondedAg")
            )

        # initialize output variables
        nonponded_ag_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeID_NonPondedAg(
            ctypes.byref(nonponded_ag_landuse_id), ctypes.byref(status)
        )

        return nonponded_ag_landuse_id.value

    def get_land_use_type_id_rice(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeID_Rice"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeID_Rice")
            )

        # initialize output variables
        rice_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeID_Rice(
            ctypes.byref(rice_landuse_id), ctypes.byref(status)
        )

        return rice_landuse_id.value

    def get_land_use_type_id_refuge(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeID_Refuge"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeID_Refuge")
            )

        # initialize output variables
        refuge_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeID_Refuge(
            ctypes.byref(refuge_landuse_id), ctypes.byref(status)
        )

        return refuge_landuse_id.value

    def get_land_use_type_id_native_riparian(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeID_NVRV"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeID_NVRV")
            )

        # initialize output variables
        nvrv_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeID_NVRV(
            ctypes.byref(nvrv_landuse_id), ctypes.byref(status)
        )

        return nvrv_landuse_id.value

    def get_land_use_ids(self):
        if not hasattr(self.dll, "IW_GetLandUseTypeIDs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLandUseTypeIDs")
            )

        # initialize output variables
        gen_ag_landuse_id = ctypes.c_int(0)
        urban_landuse_id = ctypes.c_int(0)
        nonponded_ag_landuse_id = ctypes.c_int(0)
        rice_landuse_id = ctypes.c_int(0)
        refuge_landuse_id = ctypes.c_int(0)
        nvrv_landuse_id = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLandUseTypeIDs(
            ctypes.byref(gen_ag_landuse_id),
            ctypes.byref(urban_landuse_id),
            ctypes.byref(nonponded_ag_landuse_id),
            ctypes.byref(rice_landuse_id),
            ctypes.byref(refuge_landuse_id),
            ctypes.byref(nvrv_landuse_id),
            ctypes.byref(status),
        )

        return dict(
            genag=gen_ag_landuse_id.value,
            urban=urban_landuse_id.value,
            nonpondedag=nonponded_ag_landuse_id.value,
            rice=rice_landuse_id,
            refuge=refuge_landuse_id,
            nativeriparian=nvrv_landuse_id,
        )

    def get_location_type_id_node(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_Node"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_Node")
            )

        # initialize output variables
        location_type_id_node = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_Node(
            ctypes.byref(location_type_id_node), ctypes.byref(status)
        )

        return location_type_id_node.value

    def get_location_type_id_element(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_Element"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_Element")
            )

        # initialize output variables
        location_type_id_element = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_Element(
            ctypes.byref(location_type_id_element), ctypes.byref(status)
        )

        return location_type_id_element.value

    def get_location_type_id_subregion(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_Subregion"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_Subregion")
            )

        # initialize output variables
        location_type_id_subregion = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_Subregion(
            ctypes.byref(location_type_id_subregion), ctypes.byref(status)
        )

        return location_type_id_subregion.value

    def get_location_type_id_zone(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_Zone"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_Zone")
            )

        # initialize output variables
        location_type_id_zone = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_Zone(
            ctypes.byref(location_type_id_zone), ctypes.byref(status)
        )

        return location_type_id_zone.value

    def get_location_type_id_streamnode(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_StrmNode"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_StrmNode")
            )

        # initialize output variables
        location_type_id_streamnode = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_StrmNode(
            ctypes.byref(location_type_id_streamnode), ctypes.byref(status)
        )

        return location_type_id_streamnode.value

    def get_location_type_id_streamreach(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_StrmReach"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_StrmReach")
            )

        # initialize output variables
        location_type_id_streamreach = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_StrmReach(
            ctypes.byref(location_type_id_streamreach), ctypes.byref(status)
        )

        return location_type_id_streamreach.value

    def get_location_type_id_lake(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_Lake"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_Lake")
            )

        # initialize output variables
        location_type_id_lake = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_Lake(
            ctypes.byref(location_type_id_lake), ctypes.byref(status)
        )

        return location_type_id_lake.value

    def get_location_type_id_smallwatershed(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_SmallWatershed"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_GetLocationTypeID_SmallWatershed"
                )
            )

        # initialize output variables
        location_type_id_smallwatershed = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_SmallWatershed(
            ctypes.byref(location_type_id_smallwatershed), ctypes.byref(status)
        )

        return location_type_id_smallwatershed.value

    def get_location_type_id_gwheadobs(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_GWHeadObs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_GWHeadObs")
            )

        # initialize output variables
        location_type_id_gwheadobs = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_GWHeadObs(
            ctypes.byref(location_type_id_gwheadobs), ctypes.byref(status)
        )

        return location_type_id_gwheadobs.value

    def get_location_type_id_streamhydobs(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_StrmHydObs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeID_StrmHydObs")
            )

        # initialize output variables
        location_type_id_streamhydobs = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_StrmHydObs(
            ctypes.byref(location_type_id_streamhydobs), ctypes.byref(status)
        )

        return location_type_id_streamhydobs.value

    def get_location_type_id_subsidenceobs(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_SubsidenceObs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_GetLocationTypeID_SubsidenceObs"
                )
            )

        # initialize output variables
        location_type_id_subsidenceobs = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_SubsidenceObs(
            ctypes.byref(location_type_id_subsidenceobs), ctypes.byref(status)
        )

        return location_type_id_subsidenceobs.value

    def get_location_type_id_tiledrainobs(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_TileDrainObs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_GetLocationTypeID_TileDrainObs"
                )
            )

        # initialize output variables
        location_type_id_tile_drain = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_TileDrainObs(
            ctypes.byref(location_type_id_tile_drain), ctypes.byref(status)
        )

        return location_type_id_tile_drain.value

    def get_location_type_id_streamnodebud(self):
        if not hasattr(self.dll, "IW_GetLocationTypeID_StrmNodeBud"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_GetLocationTypeID_StrmNodeBud"
                )
            )

        # initialize output variables
        location_type_id_streamnodebud = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeID_StrmNodeBud(
            ctypes.byref(location_type_id_streamnodebud), ctypes.byref(status)
        )

        return location_type_id_streamnodebud.value

    def get_location_type_ids(self):
        if not hasattr(self.dll, "IW_GetLocationTypeIDs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLocationTypeIDs")
            )

        # initialize output variables
        location_type_id_nodes = ctypes.c_int(0)
        location_type_id_element = ctypes.c_int(0)
        location_type_id_subregion = ctypes.c_int(0)
        location_type_id_zone = ctypes.c_int(0)
        location_type_id_streamnode = ctypes.c_int(0)
        location_type_id_streamreach = ctypes.c_int(0)
        location_type_id_lake = ctypes.c_int(0)
        location_type_id_smallwatershed = ctypes.c_int(0)
        location_type_id_gwheadobs = ctypes.c_int(0)
        location_type_id_streamhydobs = ctypes.c_int(0)
        location_type_id_subsidenceobs = ctypes.c_int(0)
        location_type_id_tile_drain = ctypes.c_int(0)
        location_type_id_streamnodebud = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_GetLocationTypeIDs(
            ctypes.byref(location_type_id_nodes),
            ctypes.byref(location_type_id_element),
            ctypes.byref(location_type_id_subregion),
            ctypes.byref(location_type_id_zone),
            ctypes.byref(location_type_id_lake),
            ctypes.byref(location_type_id_streamnode),
            ctypes.byref(location_type_id_streamreach),
            ctypes.byref(location_type_id_tile_drain),
            ctypes.byref(location_type_id_smallwatershed),
            ctypes.byref(location_type_id_gwheadobs),
            ctypes.byref(location_type_id_streamhydobs),
            ctypes.byref(location_type_id_subsidenceobs),
            ctypes.byref(location_type_id_streamnodebud),
            ctypes.byref(status),
        )

        return dict(
            nodes=location_type_id_nodes.value,
            elements=location_type_id_element.value,
            subregion=location_type_id_subregion.value,
            zone=location_type_id_zone.value,
            lake=location_type_id_lake.value,
            streamnode=location_type_id_streamnode.value,
            streamreach=location_type_id_streamreach.value,
            tiledrain=location_type_id_tile_drain.value,
            smallwatershed=location_type_id_smallwatershed.value,
            gwheadobs=location_type_id_gwheadobs.value,
            streamhydobs=location_type_id_streamhydobs.value,
            subsidenceobs=location_type_id_subsidenceobs.value,
            streamnodebud=location_type_id_streamnodebud.value,
        )

    def get_flow_destination_type_id_outside(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_Outside"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_Outside")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_Outside(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id_element(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_Element"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_Element")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_Element(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id_elementset(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_ElementSet"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_ElementSet")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_ElementSet(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id_gwelement(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_GWElement"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_GWElement")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_GWElement(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id_streamnode(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_StrmNode"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_StrmNode")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_StrmNode(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id_lake(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_Lake"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_Lake")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_Lake(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id_subregion(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeID_Subregion"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeID_Subregion")
            )

        # initialize output variables
        flow_destination_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeID_Subregion(
            ctypes.byref(flow_destination_type_id), ctypes.byref(status)
        )

        return flow_destination_type_id.value

    def get_flow_destination_type_id(self):
        if not hasattr(self.dll, "IW_GetFlowDestTypeIDs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetFlowDestTypeIDs")
            )

        # initialize output variables
        flow_destination_type_id_outside = ctypes.c_int(0)
        flow_destination_type_id_element = ctypes.c_int(0)
        flow_destination_type_id_elementset = ctypes.c_int(0)
        flow_destination_type_id_gwelement = ctypes.c_int(0)
        flow_destination_type_id_stream_node = ctypes.c_int(0)
        flow_destination_type_id_lake = ctypes.c_int(0)
        flow_destination_type_id_subregion = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetFlowDestTypeIDs(
            ctypes.byref(flow_destination_type_id_outside),
            ctypes.byref(flow_destination_type_id_element),
            ctypes.byref(flow_destination_type_id_elementset),
            ctypes.byref(flow_destination_type_id_gwelement),
            ctypes.byref(flow_destination_type_id_stream_node),
            ctypes.byref(flow_destination_type_id_lake),
            ctypes.byref(flow_destination_type_id_subregion),
            ctypes.byref(status),
        )

        return dict(
            outside=flow_destination_type_id_outside.value,
            stream_node=flow_destination_type_id_element.value,
            element=flow_destination_type_id_elementset.value,
            lake=flow_destination_type_id_gwelement.value,
            subregion=flow_destination_type_id_stream_node.value,
            gwelement=flow_destination_type_id_lake.value,
            elementset=flow_destination_type_id_subregion.value,
        )

    def get_supply_type_id_diversion(self):
        if not hasattr(self.dll, "IW_GetSupplyTypeID_Diversion"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetSupplyTypeID_Diversion")
            )

        # initialize output variables
        supply_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetSupplyTypeID_Diversion(
            ctypes.byref(supply_type_id), ctypes.byref(status)
        )

        return supply_type_id.value

    def get_supply_type_id_well(self):
        if not hasattr(self.dll, "IW_GetSupplyTypeID_Well"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetSupplyTypeID_Well")
            )

        # initialize output variables
        supply_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetSupplyTypeID_Well(
            ctypes.byref(supply_type_id), ctypes.byref(status)
        )

        return supply_type_id.value

    def get_supply_type_id_elempump(self):
        if not hasattr(self.dll, "IW_GetSupplyTypeID_ElemPump"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetSupplyTypeID_ElemPump")
            )

        # initialize output variables
        supply_type_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetSupplyTypeID_ElemPump(
            ctypes.byref(supply_type_id), ctypes.byref(status)
        )

        return supply_type_id.value

    def get_zone_extent_id_horizontal(self):
        if not hasattr(self.dll, "IW_GetZoneExtentID_Horizontal"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetZoneExtentID_Horizontal")
            )

        # initialize output variables
        zone_extent_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetZoneExtentID_Horizontal(
            ctypes.byref(zone_extent_id), ctypes.byref(status)
        )

        return zone_extent_id.value

    def get_zone_extent_id_vertical(self):
        if not hasattr(self.dll, "IW_GetZoneExtentID_Vertical"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetZoneExtentID_Vertical")
            )

        # initialize output variables
        zone_extent_id = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetZoneExtentID_Vertical(
            ctypes.byref(zone_extent_id), ctypes.byref(status)
        )

        return zone_extent_id.value

    def get_zone_extent_ids(self):
        if not hasattr(self.dll, "IW_GetZoneExtentID_Horizontal"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetZoneExtentID_Horizontal")
            )

        # initialize output variables
        zone_extent_id_horizontal = ctypes.c_int(0)
        zone_extent_id_vertical = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetZoneExtentIDs(
            ctypes.byref(zone_extent_id_horizontal),
            ctypes.byref(zone_extent_id_vertical),
            ctypes.byref(status),
        )

        return dict(
            horizontal=zone_extent_id_horizontal.value,
            vertical=zone_extent_id_vertical.value,
        )

    def get_budget_type_ids(self):
        if not hasattr(self.dll, "IW_GetBudgetTypeIDs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetBudgetTypeIDs")
            )

        # initialize output variables
        budget_type_id_gw = ctypes.c_int(0)
        budget_type_id_rootzone = ctypes.c_int(0)
        budget_type_id_lwu = ctypes.c_int(0)
        budget_type_id_npcrop_rz = ctypes.c_int(0)
        budget_type_id_npcrop_lwu = ctypes.c_int(0)
        budget_type_id_pcrop_rz = ctypes.c_int(0)
        budget_type_id_pcrop_lwu = ctypes.c_int(0)
        budget_type_id_unsat_zone = ctypes.c_int(0)
        budget_type_id_stream_node = ctypes.c_int(0)
        budget_type_id_stream_reach = ctypes.c_int(0)
        budget_type_id_div_detail = ctypes.c_int(0)
        budget_type_id_smallwatershed = ctypes.c_int(0)
        budget_type_id_lake = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetBudgetTypeIDs(
            ctypes.byref(budget_type_id_gw),
            ctypes.byref(budget_type_id_rootzone),
            ctypes.byref(budget_type_id_lwu),
            ctypes.byref(budget_type_id_npcrop_rz),
            ctypes.byref(budget_type_id_npcrop_lwu),
            ctypes.byref(budget_type_id_pcrop_rz),
            ctypes.byref(budget_type_id_pcrop_lwu),
            ctypes.byref(budget_type_id_unsat_zone),
            ctypes.byref(budget_type_id_stream_node),
            ctypes.byref(budget_type_id_stream_reach),
            ctypes.byref(budget_type_id_div_detail),
            ctypes.byref(budget_type_id_smallwatershed),
            ctypes.byref(budget_type_id_lake),
            ctypes.byref(status),
        )

        return dict(
            gw=budget_type_id_gw.value,
            rootzone=budget_type_id_rootzone.value,
            lwu=budget_type_id_lwu.value,
            npcrop_rz=budget_type_id_npcrop_rz.value,
            npcrop_lwu=budget_type_id_npcrop_lwu.value,
            pcrop_rz=budget_type_id_pcrop_rz.value,
            pcrop_lwu=budget_type_id_pcrop_lwu.value,
            unsat_zone=budget_type_id_unsat_zone.value,
            stream_node=budget_type_id_stream_node.value,
            stream_reach=budget_type_id_stream_reach.value,
            div_detail=budget_type_id_div_detail.value,
            smallwatershed=budget_type_id_smallwatershed.value,
            lake=budget_type_id_lake.value,
        )

    def get_zbudget_type_ids(self):
        if not hasattr(self.dll, "IW_GetZBudgetTypeIDs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetZBudgetTypeIDs")
            )

        # initialize output variables
        zbudget_type_id_gw = ctypes.c_int(0)
        zbudget_type_id_rootzone = ctypes.c_int(0)
        zbudget_type_id_lwu = ctypes.c_int(0)
        zbudget_type_id_unsatzone = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_GetZBudgetTypeIDs(
            ctypes.byref(zbudget_type_id_gw),
            ctypes.byref(zbudget_type_id_rootzone),
            ctypes.byref(zbudget_type_id_lwu),
            ctypes.byref(zbudget_type_id_unsatzone),
            ctypes.byref(status),
        )

        return dict(
            gw=zbudget_type_id_gw.value,
            rootzone=zbudget_type_id_rootzone.value,
            lwu=zbudget_type_id_lwu.value,
            unsat_zone=zbudget_type_id_unsatzone.value,
        )

    def get_version(self):
        """returns the version of the IWFM DLL"""
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetVersion"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetVersion")
            )

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # set version character array length to 500
        version_length = ctypes.c_int(600)

        # initialize output variables
        iwfm_version = ctypes.create_string_buffer(version_length.value)

        self.dll.IW_GetVersion(
            ctypes.byref(version_length), iwfm_version, ctypes.byref(self.status)
        )

        iwfm_version_string = iwfm_version.value.decode("utf-8")

        iwfm_version_info = {
            val.split(":")[0]: val.split(":")[1].strip()
            for val in iwfm_version_string.split("\n")
        }

        return iwfm_version_info

    def get_n_intervals(
        self, begin_date, end_date, time_interval, includes_end_date=True
    ):
        """returns the number of time intervals between a provided start date and end date

        Parameters
        ----------
        begin_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        end_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        time_interval : str
            valid IWFM time interval

        includes_end_date : boolean, default=True
            True adds 1 to the number of intervals to include the
            end_date
            False is the number of intervals between the two dates
            without including the end_date

        Returns
        -------
        int
            number of time intervals between begin and end date

        See Also
        --------
        IWFMModel.get_current_date_and_time : returns the current simulation date and time
        IWFMModel.get_n_time_steps : returns the number of timesteps in an IWFM simulation
        IWFMModel.get_time_specs : returns the IWFM simulation dates and time step
        IWFMModel.get_output_interval : returns a list of the possible time intervals a selected time-series data can be retrieved at.
        IWFMModel.is_date_greater : returns True if first_date is greater than comparison_date
        IWFMModel.increment_time : increments the date provided by the specified time interval

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.get_n_intervals('06/30/1997_24:00', '12/31/1997_24:00', '1MON', includes_end_date=False)
        6
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.get_n_intervals('09/30/2011_24:00', '12/31/2011_24:00', '1DAY')
        92
        >>> model.kill()
        """
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetNIntervals"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetNIntervals")
            )

        # check that begin_date is valid
        self._validate_iwfm_date(begin_date)

        # check that end_date is valid
        self._validate_iwfm_date(end_date)

        # check that time_interval is a valid IWFM time_interval
        self._validate_time_interval(time_interval)

        # check that begin_date is not greater than end_date
        if self.is_date_greater(begin_date, end_date):
            raise ValueError("begin_date must occur before end_date")

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # convert IWFM dates to ctypes character arrays
        begin_date = ctypes.create_string_buffer(begin_date.encode("utf-8"))
        end_date = ctypes.create_string_buffer(end_date.encode("utf-8"))
        time_interval = ctypes.create_string_buffer(time_interval.encode("utf-8"))

        # set length of IWFM datetime string
        length_iwfm_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # set length of IWFM time_interval string
        length_time_interval = ctypes.c_int(ctypes.sizeof(time_interval))

        # initialize output variables
        n_intervals = ctypes.c_int(0)

        self.dll.IW_GetNIntervals(
            begin_date,
            end_date,
            ctypes.byref(length_iwfm_date),
            time_interval,
            ctypes.byref(length_time_interval),
            ctypes.byref(n_intervals),
            ctypes.byref(self.status),
        )

        if includes_end_date:
            return n_intervals.value + 1

        return n_intervals.value

    def increment_time(self, date_string, time_interval, n_intervals):
        """increments the date provided by the specified time interval

        Parameters
        ----------
        date_string : str
            IWFM date format i.e. MM/DD/YYYY_HH:MM

        time_interval : str
            valid time interval

        n_intervals : int
            number of intervals to increment time

        Returns
        -------
        str
            IWFM-style date the number of time intervals after the provided
            date

        See Also
        --------
        IWFMModel.get_current_date_and_time : returns the current simulation date and time
        IWFMModel.get_n_time_steps : returns the number of timesteps in an IWFM simulation
        IWFMModel.get_time_specs : returns the IWFM simulation dates and time step
        IWFMModel.get_n_intervals : returns the number of time intervals between a provided start date and end date
        IWFMModel.get_output_interval : returns a list of the possible time intervals a selected time-series data can be retrieved at.
        IWFMModel.is_date_greater : returns True if first_date is greater than comparison_date

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.increment_time('10/01/1990_24:00', '1DAY', n_intervals=1)
        '10/02/1990_24:00'
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.increment_time('12/31/2000_24:00', '1MON', n_intervals=3)
        '03/31/2001_24:00'
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.increment_time('02/28/1991_24:00', '1YEAR', n_intervals=1)
        '02/29/1992_24:00'
        >>> model.kill()
        """
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_IncrementTime"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_IncrementTime")
            )

        # check that date is valid
        self._validate_iwfm_date(date_string)

        # check that time_interval is a valid IWFM time_interval
        self._validate_time_interval(time_interval)

        # convert date_string to ctypes character array
        date_string = ctypes.create_string_buffer(date_string.encode("utf-8"))

        # get length of iwfm_date string
        len_date_string = ctypes.c_int(ctypes.sizeof(date_string))

        # convert time_interval to ctypes character array
        time_interval = ctypes.create_string_buffer(time_interval.encode("utf-8"))

        # get lengh of time_interval
        len_time_interval = ctypes.c_int(ctypes.sizeof(time_interval))

        # convert n_intervals to ctypes
        n_intervals = ctypes.c_int(n_intervals)

        # initialize output variables
        status = ctypes.c_int(-1)

        self.dll.IW_IncrementTime(
            ctypes.byref(len_date_string),
            date_string,
            ctypes.byref(len_time_interval),
            time_interval,
            ctypes.byref(n_intervals),
            ctypes.byref(status),
        )

        return date_string.value.decode("utf-8")

    def is_date_greater(self, first_date, comparison_date):
        """returns True if first_date is greater than comparison_date

        Parameters
        ----------
        first_date : str
            IWFM date format MM/DD/YYYY_HH:MM

        comparison_date : str
            IWFM date format MM/DD/YYYY_HH:MM

        Returns
        -------
        boolean
            True if first_date is greater (in the future) when compared to the comparison_date
            False if first_date is less (in the past) when compared to the comparison_date

        See Also
        --------
        IWFMModel.get_current_date_and_time : returns the current simulation date and time
        IWFMModel.get_n_time_steps : returns the number of timesteps in an IWFM simulation
        IWFMModel.get_time_specs : returns the IWFM simulation dates and time step
        IWFMModel.get_n_intervals : returns the number of time intervals between a provided start date and end date
        IWFMModel.get_output_interval : returns a list of the possible time intervals a selected time-series data can be retrieved at.
        IWFMModel.increment_time : increments the date provided by the specified time interval

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.is_date_greater('09/30/2011_24:00', '10/01/2011_24:00')
        False
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, preprocessor_infile, simulation_infile)
        >>> model.is_date_greater('03/28/2001_24:00', '06/30/1989_24:00')
        True
        >>> model.kill()
        """
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_IsTimeGreaterThan"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_IsTimeGreaterThan")
            )

        # check that first_date is valid
        self._validate_iwfm_date(first_date)

        # check that comparison_date is valid
        self._validate_iwfm_date(comparison_date)

        # convert begin and end dates to ctypes character arrays
        first_date = ctypes.create_string_buffer(first_date.encode("utf-8"))
        comparison_date = ctypes.create_string_buffer(comparison_date.encode("utf-8"))

        # set length of IWFM date
        length_dates = ctypes.c_int(ctypes.sizeof(first_date))

        # initialize output variables
        compare_result = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        self.dll.IW_IsTimeGreaterThan(
            ctypes.byref(length_dates),
            first_date,
            comparison_date,
            ctypes.byref(compare_result),
            ctypes.byref(status),
        )

        if compare_result.value == -1:
            is_greater = False
        elif compare_result.value == 1:
            is_greater = True

        return is_greater

    def set_log_file(self, file_name="message.log"):
        """opens a text log file to print out error and warning messages

        Parameters
        ----------
        file_name : str, default='message.log'
            name of the log file used to write error and warning messages

        Returns
        -------
        None
            opens the log file
        """
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_SetLogFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_SetLogFile")
            )

        # convert file_name to ctypes character array
        file_name = ctypes.create_string_buffer(file_name.encode("utf-8"))

        # get length of file_name
        len_file_name = ctypes.c_int(ctypes.sizeof(file_name))

        # initialize output variables
        status = ctypes.c_int(-1)

        self.dll.IW_SetLogFile(
            ctypes.byref(len_file_name), file_name, ctypes.byref(status)
        )

    def close_log_file(self):
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_CloseLogFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_CloseLogFile")
            )

        # initialize output variables
        status = ctypes.c_int(-1)

        self.dll.IW_CloseLogFile(ctypes.byref(status))

    def get_last_message(self):
        """the error message in case a procedure call from IWFM API
        returns an error code (status) other than 0

        Returns
        -------
        str
            error message for the procedure if it returns an error code
        """
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetLastMessage"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLastMessage")
            )

        # set length of last_message to 500
        length_message = ctypes.c_int(500)

        # character array
        last_message = ctypes.create_string_buffer(length_message.value)

        # initialize output variables
        status = ctypes.c_int(-1)

        self.dll.IW_GetLastMessage(
            ctypes.byref(length_message), last_message, ctypes.byref(status)
        )

        return last_message.value.decode("utf-8")

    def log_last_message(self):
        """prints the last error message (generated when a procedure call
        from IWFM API returns an error code (status) other than 0) to the
        message log file
        """
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetLastMessage"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_GetLastMessage")
            )

        # initialize output variables
        status = ctypes.c_int(-1)

        self.dll.IW_LogLastMessage(ctypes.byref(status))

    def _is_time_interval_greater_or_equal(
        self, time_interval, simulation_time_interval
    ):
        """determines if a provided time_interval is greater than or
        equal to the simulation_time_interval

        Parameters
        ----------
        time_interval : str
            valid IWFM time interval to compare with the simulation time
            interval

        simulation_time_interval : str
            valid IWFM time interval representing the simulation time
            interval

        Returns
        -------
        boolean
            True if time interval is greater than or equal to
            simulation time interval, otherwise False
        """
        # validate time interval
        self._validate_time_interval(time_interval)

        # validate simulation_time_interval
        self._validate_time_interval(simulation_time_interval)

        # list of valid time intervals
        _valid_time_intervals = [
            "1MIN",
            "2MIN",
            "3MIN",
            "4MIN",
            "5MIN",
            "10MIN",
            "15MIN",
            "20MIN",
            "30MIN",
            "1HOUR",
            "2HOUR",
            "3HOUR",
            "4HOUR",
            "6HOUR",
            "8HOUR",
            "12HOUR",
            "1DAY",
            "1WEEK",
            "1MON",
            "1YEAR",
        ]

        index_time_interval = _valid_time_intervals.index(time_interval)
        index_simulation_interval = _valid_time_intervals.index(
            simulation_time_interval
        )

        if index_time_interval >= index_simulation_interval:
            return True
        else:
            return False

    def _validate_iwfm_date(self, dt):
        """performs validation that a provided value is an IWFM-format date string based on
        string length and format MM/DD/YYYY_HH:MM

        Parameters
        ----------
        dt : str
            input value to check if IWFM-format date

        Returns
        -------
        None
            raises errors if validation checks do not pass
        """
        if not isinstance(dt, str):
            raise TypeError("IWFM dates must be a string")

        if len(dt) != 16:
            raise ValueError(
                "IWFM dates must be 16 characters in length and of format MM/DD/YYYY_HH:MM"
            )

        if "_" not in dt or dt.index("_") != 10:
            raise ValueError("IWFM dates must have an '_' separating the date and time")

        if ":" not in dt or dt.index(":") != 13:
            raise ValueError(
                "IWFM dates must have an ':' separating the hours from minutes"
            )

        if dt[2] != "/" or dt[5] != "/":
            raise ValueError(
                "IWFM dates must use '/' as separators for the month, day, year in the date"
            )

        try:
            datetime.datetime.strptime(dt, "%m/%d/%Y_%H:%M")
        except ValueError:
            try:
                datetime.datetime.strptime(dt.split("_")[0], "%m/%d/%Y")
            except ValueError:
                raise ValueError(
                    "Value provided: {} could not be converted to a date".format(dt)
                )
            else:
                try:
                    hour = int(dt[11:13])
                    minute = int(dt[14:])
                except:
                    raise ValueError("hour or minute values are not numbers")
                else:
                    if hour < 0 or hour > 24:
                        raise ValueError("hour value is not between 00 and 24")

                    if minute < 0 or minute > 59:
                        raise ValueError("minute value is not between 00 and 59")

                    if hour == 24 and minute > 0:
                        raise ValueError("days cannot exceed 24:00 hours")

    def _validate_time_interval(self, time_interval):
        """performs validation that a provided value is an IWFM-format time-interval string

        Parameters
        ----------
        time_interval : str (not case-sensitive)
            input value to check if IWFM-format time-interval

        Returns
        -------
        None
            raises errors if validation checks do not pass
        """
        # check input type is a string
        if not isinstance(time_interval, str):
            raise TypeError(
                "time_interval must be a string. type entered is {}.".format(
                    type(time_interval)
                )
            )

        # list of valid time intervals
        _valid_time_intervals = [
            "1MIN",
            "2MIN",
            "3MIN",
            "4MIN",
            "5MIN",
            "10MIN",
            "15MIN",
            "20MIN",
            "30MIN",
            "1HOUR",
            "2HOUR",
            "3HOUR",
            "4HOUR",
            "6HOUR",
            "8HOUR",
            "12HOUR",
            "1DAY",
            "1WEEK",
            "1MON",
            "1YEAR",
        ]

        if time_interval.upper() not in _valid_time_intervals:
            error_string = (
                "time_interval entered is not a valid IWFM time interval.\n"
                + "time_interval must be:\n\t-{}".format(
                    "\n\t-".join(_valid_time_intervals)
                )
            )
            raise ValueError(error_string)

    def _string_to_list_by_array(
        self, in_string, starting_position_array, length_output_list
    ):
        """converts a string to a list of strings based on an
        array of the starting character position (index).

        Parameters
        ----------
        in_string : str or ctypes.Array (character array)
            input string that is converted to list of strings

        starting_position_array : np.array, list of ints, ctypes.Array
            array of starting character index for each value in list.

        length_output_list : int, ctypes.c_int, ctypes.c_long
            number of non-placeholder values in starting_position_array

        Returns
        -------
        list of strings
            input string (in_string) sliced into pieces based on array
            of starting positions (starting_position_array)

        Notes
        -----
        length of starting_position_array will be the length of the output list
        """
        # check that type of starting_position_array is a np.ndarray, list, tuple, or ctypes.Array
        if not isinstance(
            starting_position_array, (np.ndarray, list, tuple, ctypes.Array)
        ):
            raise TypeError(
                "starting_position_array must be a np.ndarray, list, tuple, ctypes.Array"
            )

        # handle case where starting_position_array is a list, tuple, or ctypes.Array
        if isinstance(starting_position_array, (list, tuple, ctypes.Array)):

            # convert to a numpy array
            starting_position_array = np.array(starting_position_array)

        # check that all values are integers
        if starting_position_array.dtype not in (np.int, np.int32, np.dtype("<i4")):
            raise TypeError("All values in starting_position_array must be type: int.")

        # check that length_output_list is an integer
        if not isinstance(length_output_list, (int, ctypes.c_long, ctypes.c_int)):
            raise TypeError(
                "length_output_list must be an int, ctypes.c_int, or ctypes.c_long."
            )

        # convert length_output_list to python integer
        if isinstance(length_output_list, (ctypes.c_long, ctypes.c_int)):
            length_output_list = length_output_list.value

        # check that in_string is a string
        if not isinstance(in_string, (str, ctypes.Array)):
            raise TypeError(
                "in_string must be type string or ctypes.Array.\n"
                + "Type given was {}".format(type(in_string))
            )

        # convert in_string to a python string if in_string is a ctypes character array
        if isinstance(in_string, ctypes.Array):
            in_string = in_string.value.decode("utf-8")

        # initialize empty list for values
        string_list = []

        # trim starting_position_array to length_output_list
        if length_output_list > 0:
            starting_position_array = starting_position_array[:length_output_list]

            # check if first value in array is 1
            if starting_position_array[0] == 1:
                # first python arrays are 0-indexed and the resulting delimiter_position_array
                # is 1-indexed (fortran-standard)
                position_array = starting_position_array - 1

            else:
                position_array = starting_position_array

            for i in range(len(position_array)):
                if position_array[i] != position_array[-1]:
                    string_list.append(
                        in_string[position_array[i] : position_array[i + 1]]
                    )
                else:
                    string_list.append(in_string[position_array[i] :])

        return [val.strip() for val in string_list]
