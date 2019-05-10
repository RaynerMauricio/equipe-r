# This code creates a epJSON file (EnergyPlus model), according to the
# input parameters defined on the main function.
#
# Notice that the names given to the surfaces go from 0 to 3 clockwise,
# being: 0 up, 1 right, 2 down, and 3 left. 
'''
                    side 0
         _______________________________
        |                               |
        |                               |
        |                               |
        |                               |
        |                               |
  side3 |         floor plan            |   side 1
        |                               |
        |                               |
        |                               |
        |_______________________________|

                    side 2
'''

from cp_calc_res import cp_calc
from concrete_eps import concrete_wall
from dict_update import update
import json
from hive import hive
import os
import math

EMS_PROGRAM_FILE = 'ems_program.json'

def shadingjson(x0, y0, z0, x1, y1, z1, x2, y2, z2, x3, y3, z3):
    return {
                "idf_max_extensible_fields": 12,
                "idf_max_fields": 15,
                'transmittance_schedule_name': '',
                'number_of_vertices': 4,
                "vertices": [
                    {
                    "vertex_x_coordinate": x0,
                    "vertex_y_coordinate": y0,
                    "vertex_z_coordinate": z0
                    },
                    {
                    "vertex_x_coordinate": x1,
                    "vertex_y_coordinate": y1,
                    "vertex_z_coordinate": z1
                    },
                    {
                    "vertex_x_coordinate": x2,
                    "vertex_y_coordinate": y2,
                    "vertex_z_coordinate": z2
                    },
                    {
                    "vertex_x_coordinate": x3,
                    "vertex_y_coordinate": y3,
                    "vertex_z_coordinate": z3
                    }
                ]
            }    

def main(zone_area=8.85, zone_ratio=1.179, zone_height=2.5, azimuth=90,
    absorptance=.5, wall_u=4.083, wall_ct=165.6, ground=0, roof=1, 
    shading=[0,0.5,0,0], shading_type = [0,0,0,0], surrounding_shading = [0,30,0,0], nearness = 4,
    surrounding_horizontal_left = [0,0,0,0], surrounding_horizontal_right = [0,0,0,0],
    shading_vertical_left = [0,0,0,0], shading_vertical_right = [0,0,0,0],
    shading_vertical_left_type = [0,0,0,0], shading_vertical_right_type = [0,0,0,0],
    living_room = False, exp=[1,1,0,0],
    wwr=[0,0.219,0,0], opening_type=[0,1,0,0], open_fac=[0,0.45,0,0], glass_fs=.87, equipment=0,
    lights = 5, bldg_ratio=0.85, floor_height=0, ela_area = 0.7, equipment_hive = 100, bound='hive',
    input_file='seed.json', output='teste_model.epJSON',
    construction="", convert=False):
    
    ## Main function that creates the epJSON model.
    
    ## INPUTS:
    ## zone_area - The area of the "APP" in square meters.
    ## zone_ratio - Ratio between y length (walls 1 and 3), and xlength
    #  (walls 0 and 2). Or: Ratio = zone_y/zone_x.
    ## zone_height - Distance from floor to ceiling in meters.
    ## azimuth - Angle from north.
    ## absorptance - The value of the absorptace of walls and roof.
    ## wall_u - The value of transmittance of the walls (concrete+eps 
    # approach only).
    ## wall_ct - The value of thermal capacity of the walls (concrete+eps 
    # approach only).
    ## ground - Condition of exposure: 0 = Adiabatic, 1 = Outdoors.
    ## roof - Condition of exposure: 0 = Adiabatic, 1 = Outdoors.
    ## shading - the length of horizontal shading in meters.
    ## surrounding_shading - The vertical angle of the permanent surrounding shading (building, tree, topograph...)
    ## surrounding_horizontal_left and right are the horizontal angle in degree used to obtain the surrounding width
    ## living_room - Defines schedules for occupation: True = living 
    #  room occupation pattern, False = bedroom occupation pattern.
    ## exp - List with condition of exposure of walls: 0 = not exposed,
    #  1 = exposed (Outdoors).
    ## wwr - List with WWR of the walls.
    ## opening_type - 0 = window and 1 = door
    ## open_fac - List with the opening factors of windows.
    ## glass_fs - SHGC of the windows' glass.
    ## equipment - Equipment loads in Watts
    ## lights - Lights loads in Watts per square meters.
    ## bldg_ratio - The ratio of the reference building.
    ## floor_height - Distance from zone's floor to the ground in meters.
    ## ela_area - 0.7 = porta tipical aberta; 0.4333 = porta pequena aberta; porta fechada < 0.01
    ## bound - String that defines the boundary condition of internal 
    #  walls. May be "hive", "double", or "adiabatic".
    ## input_file - The name of the seed file. The seed files contains
    #  the information that do not depend on the input variables.
    ## output - The name of the generated epJSON model.
    ## construction - The name of a json file with a construction object
    # called "wall_construction" and the materials objects.
    ## convert - Condition to generate a .idf model. energyplus has to 
    # be an environment variable for it to work!

    print(output)
    
    #### Defining zone's x and y length --------------------------------
    zone_x = (zone_area/zone_ratio)**(1/2)
    zone_y = (zone_area /zone_x)
    
    #### Defining Occupation condition ---------------------------------
    
    if living_room:
        occupation_sch = 'livingroom_occup'
        light_sch = 'livingroom_lights'
        activity_sch = 'livingroom_activity'
        number_of_people = 4
    else:
        occupation_sch = 'bedroom_occup'
        light_sch = 'bedroom_lights'
        activity_sch = 'bedroom_activity'
        number_of_people = 2

    #### START BUILDING OBJECTS ----------------------------------------
    model = dict()

    ##### Building -----------------------------------------------------
    model["Building"] = {
        output[:-7]: {
            "north_axis": azimuth,
            "loads_convergence_tolerance_value": 0.04,
            "maximum_number_of_warmup_days": 25,
            "solar_distribution": "FullInteriorAndExteriorWithReflections",
            "temperature_convergence_tolerance_value": 0.4,
            "idf_max_extensible_fields": 0,
            "idf_max_fields": 8,
            "terrain": "City"
        }
    }

    ##### ZONE ---------------------------------------------------------
    model["Zone"] = {
        "room": {
            "z_origin": floor_height
        }
    }

    ##### Building Surface ---------------------------------------------
    model["BuildingSurface:Detailed"] = {

        # Ceiling
        "ceiling": {
            "vertices": [
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": zone_height
                }
            ]
        },

        # Floor
        "floor": {
            "vertices": [
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": 0.0
                }
            ]
        },

        # Walls: 0 = up, 1 = right, 2 = down, 3 = left
        "wall-0": {
            "vertices": [
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": zone_height
                }
            ]
        },
        "wall-1": {
            "vertices": [
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": zone_height
                }
            ]
        },
        "wall-2": {
            "vertices": [
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": zone_x,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": zone_height
                }
            ]
        },
        "wall-3": {
            "vertices": [
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": zone_height
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": zone_y,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": 0.0
                },
                {
                    "vertex_x_coordinate": 0.0,
                    "vertex_y_coordinate": 0.0,
                    "vertex_z_coordinate": zone_height
                }
            ]
        }
    }

    # Top Condition
    if roof == 0:
        ceiling_bound = {
            "outside_boundary_condition": "Adiabatic",
            "sun_exposure": "NoSun",
            "surface_type": "Ceiling",
            "wind_exposure": "NoWind"
        }

    else:
        ceiling_bound = {
            "outside_boundary_condition": "Outdoors",
            "sun_exposure": "SunExposed",
            "surface_type": "Roof",
            "wind_exposure": "WindExposed"
        }

    model["BuildingSurface:Detailed"]["ceiling"].update(ceiling_bound)

    # Bottom condition
    if ground == 0:
        ground_bound = {
            "outside_boundary_condition": "Adiabatic",
            "outside_boundary_condition_object": "",
            "sun_exposure": "NoSun",
            "wind_exposure": "NoWind"
        }

    else:
        if floor_height == 0:
            ground_bound = {
                "outside_boundary_condition": "OtherSideConditionsModel",
                "outside_boundary_condition_object": "GroundCoupledOSCM",
                "sun_exposure": "NoSun",
                "wind_exposure": "NoWind"
            }
            model["SurfaceProperty:OtherSideConditionsModel"] = {
                "GroundCoupledOSCM": {
                    "idf_max_extensible_fields": 0,
                    "idf_max_fields": 2,
                    "type_of_modeling": "GroundCoupledSurface"
                }
            }
            model["Site:GroundDomain:Slab"] = {
                "GroundDomain": {
                    "aspect_ratio": 1,
                    "evapotranspiration_ground_cover_parameter": 0.4,
                    "geometric_mesh_coefficient": 1.6,
                    "ground_domain_depth": 10,
                    "horizontal_insulation": "No",
                    "horizontal_insulation_extents": "Full",
                    "idf_max_extensible_fields": 0,
                    "idf_max_fields": 25,
                    "mesh_density_parameter": 6,
                    "perimeter_offset": 5,
                    "simulation_timestep": "Timestep",
                    "slab_boundary_condition_model_name": "GroundCoupledOSCM",
                    "slab_location": "OnGrade",
                    "soil_density": 1250,
                    "soil_moisture_content_volume_fraction": 30,
                    "soil_moisture_content_volume_fraction_at_saturation": 50,
                    "soil_specific_heat": 1500,
                    "soil_thermal_conductivity": 1.5,
                    "undisturbed_ground_temperature_model_name": "FiniteDiff",
                    "undisturbed_ground_temperature_model_type": "Site:GroundTemperature:Undisturbed:FiniteDifference",
                    "vertical_insulation": "No"
                }
            }
            model["Site:GroundTemperature:Undisturbed:FiniteDifference"] = {
                "FiniteDiff": {
                    "evapotranspiration_ground_cover_parameter": 0.4,
                    "idf_max_extensible_fields": 0,
                    "idf_max_fields": 7,
                    "soil_density": 1250,
                    "soil_moisture_content_volume_fraction": 30,
                    "soil_moisture_content_volume_fraction_at_saturation": 50,
                    "soil_specific_heat": 1500,
                    "soil_thermal_conductivity": 1.5
                }
            }
        else:
            ground_bound = {
                "outside_boundary_condition": "Outdoors",
                "outside_boundary_condition_object": "",
                "sun_exposure": "NoSun",
                "wind_exposure": "WindExposed"
            }

    #model["BuildingSurface:Detailed"]["floor"].update(ground_bound)
    update(model["BuildingSurface:Detailed"]["floor"],ground_bound)
    
    # Wall exposition condition
    exposed_wall = {
        "outside_boundary_condition": "Outdoors",
        "sun_exposure": "SunExposed",
        "wind_exposure": "WindExposed"
    }
    adiabatic_wall = {
        "outside_boundary_condition": "Adiabatic",
        "sun_exposure": "NoSun",
        "wind_exposure": "NoWind"
    }
    hive_wall = {
        "outside_boundary_condition": "Surface",
        "sun_exposure": "NoSun",
        "wind_exposure": "NoWind"
    }

    if sum(exp) < 4:
        model['AirflowNetwork:MultiZone:Zone'] = {}
        
        model["AirflowNetwork:MultiZone:Surface:EffectiveLeakageArea"] = {
            "ela": {
                "air_mass_flow_exponent": 0.65,
                "discharge_coefficient": 1,
                "effective_leakage_area": ela_area,
                "reference_pressure_difference": 4,
                "idf_max_extensible_fields": 0,
                "idf_max_fields": 5
            }
        }
        
        hive_elas = {}
        hive_externalnodes = {}
        
    for i in range(4):
        
        if exp[i] > 0:
            model["BuildingSurface:Detailed"]["wall-"+str(i)].update(exposed_wall)

        else:
            # airflownetwork ela
            if bound == 'hive':
                model["BuildingSurface:Detailed"]["wall-"+str(i)].update(hive_wall)
                model["BuildingSurface:Detailed"]["wall-"+str(i)]["outside_boundary_condition_object"] = "hive_"+str(i)+"_wall-"+str((i+2)%4)
                model["Zone"]["hive_" +str(i)], hive_afn, hive_surfaces = hive(i, zone_x, zone_y, zone_height,floor_height, ground, roof)

                model["ElectricEquipment"] = {
                    "equipment_loads_hive_" +str(i): {
                    "design_level": equipment_hive,
                    "design_level_calculation_method": "EquipmentLevel",
                    "end_use_subcategory": "General",
                    "fraction_latent": 0,
                    "fraction_lost": 0,
                    "fraction_radiant": 0.3,
                    "idf_max_extensible_fields": 0,
                    "idf_max_fields": 11,
                    "schedule_name": "livingroom_equipment",
                    "zone_or_zonelist_name": "hive_" +str(i)
                    }
                }

                afn_zone = hive_afn['zone']
                elas_return = hive_afn['elas']
                externalnodes_return = hive_afn['nodes']
                
                model['AirflowNetwork:MultiZone:Zone'].update(afn_zone)
                model["BuildingSurface:Detailed"].update(hive_surfaces)
                hive_elas.update(elas_return)
                hive_externalnodes.update(externalnodes_return)

            elif bound == 'double' or bound == 'doublewall':
                model["BuildingSurface:Detailed"]["wall-"+str(i)].update(exposed_wall)
                model["BuildingSurface:Detailed"]["wall-"+str(i)]["construction_name"] = "wall_construction_double"
            else:
                model["BuildingSurface:Detailed"]["wall-"+str(i)].update(adiabatic_wall)

    #### FENESTRATION --------------------------------------------------
    
    larguras_x1 = [None for i in range(4)]
    larguras_x2 = [None for i in range(4)]
    larguras_y1 = [None for i in range(4)]
    larguras_y2 = [None for i in range(4)]
    alturas_z1 = [None for i in range(4)]
    alturas_z2 = [None for i in range(4)]

    model["FenestrationSurface:Detailed"] = {}
    for i in range(4):
        
        if wwr[i] > 0:
                        
            if i == 0:
                
                wallArea = zone_x*zone_height
                windowArea = wallArea*wwr[i]
                wallAspectRatio = zone_height/zone_x

                altura = (windowArea*wallAspectRatio)**0.5
                largura = windowArea/altura

                if opening_type[i] == 0:
                    window_x2 = (zone_x-largura)/2
                    window_x1 = zone_x - window_x2
                    window_y1 = zone_y
                    window_y2 = zone_y                    
                    window_z1 = (zone_height-altura)/2
                    window_z2 = zone_height - window_z1

                else:
                    door_height = 2.1
                    largura = windowArea/door_height

                    if largura > zone_x:                        
                        largura = windowArea/altura
                        window_x2 = (zone_x-largura)/2
                        window_x1 = zone_x - window_x2
                        window_y1 = zone_y
                        window_y2 = zone_y                        
                        window_z1 = 0
                        window_z2 = altura                    
                    
                    else:
                        largura = windowArea/door_height
                        window_x2 = (zone_x - largura)/2
                        window_x1 = zone_x - window_x2
                        window_y1 = zone_y
                        window_y2 = zone_y                   
                        window_z1 = 0
                        window_z2 = door_height

                larguras_x1[i] = window_x1
                larguras_x2[i] = window_x2
                larguras_y1[i] = window_y1
                larguras_y2[i] = window_y2
                alturas_z1[i] = window_z1
                alturas_z2[i] = window_z2

            elif i == 1:
                
                wallArea = zone_y*zone_height
                windowArea = wallArea*wwr[i]
                wallAspectRatio = zone_height/zone_y

                altura = (windowArea*wallAspectRatio)**0.5
                largura = windowArea/altura

                if opening_type[i] == 0:
                    window_x1 = zone_x
                    window_x2 = zone_x
                    window_y1 = (zone_y-largura)/2
                    window_y2 = zone_y - window_y1                    
                    window_z1 = (zone_height-altura)/2
                    window_z2 = zone_height - window_z1                  

                else:
                    door_height = 2.1
                    largura = windowArea/door_height

                    if largura > zone_y:                        
                        largura = windowArea/altura
                        window_x1 = zone_x
                        window_x2 = zone_x
                        window_y1 = (zone_y-largura)/2
                        window_y2 = zone_y - window_y1                    
                        window_z1 = 0
                        window_z2 = altura
                    
                    else:
                        largura = windowArea/door_height
                        window_x1 = zone_x
                        window_x2 = zone_x
                        window_y1 = (zone_y-largura)/2
                        window_y2 = zone_y - window_y1                    
                        window_z1 = 0
                        window_z2 = door_height

                larguras_x1[i] = window_x1
                larguras_x2[i] = window_x2
                larguras_y1[i] = window_y1
                larguras_y2[i] = window_y2
                alturas_z1[i] = window_z1
                alturas_z2[i] = window_z2

            elif i == 2:
            
                wallArea = zone_x*zone_height
                windowArea = wallArea*wwr[i]
                wallAspectRatio = zone_height/zone_x

                altura = (windowArea*wallAspectRatio)**0.5
                largura = windowArea/altura

                if opening_type[i] == 0:
                    window_x1 = (zone_x-largura)/2
                    window_x2 = zone_x - window_x1
                    window_y1 = 0
                    window_y2 = 0
                    window_z1 = (zone_height-altura)/2
                    window_z2 = zone_height - window_z1

                else:
                    door_height = 2.1
                    largura = windowArea/door_height

                    if largura > zone_x:                        
                        largura = windowArea/altura
                        window_x1 = (zone_x-largura)/2
                        window_x2 = zone_x - window_x1
                        window_y1 = 0
                        window_y2 = 0
                        window_z1 = 0
                        window_z2 = altura

                    else:
                        largura = windowArea/door_height
                        window_x1 = (zone_x-largura)/2
                        window_x2 = zone_x - window_x1
                        window_y1 = 0
                        window_y2 = 0
                        window_z1 = 0
                        window_z2 = door_height   
                
                larguras_x1[i] = window_x1
                larguras_x2[i] = window_x2
                larguras_y1[i] = window_y1
                larguras_y2[i] = window_y2
                alturas_z1[i] = window_z1
                alturas_z2[i] = window_z2

            else:
            
                wallArea = zone_y*zone_height
                windowArea = wallArea*wwr[i]
                wallAspectRatio = zone_height/zone_y

                altura = (windowArea*wallAspectRatio)**0.5
                largura = windowArea/altura

                if opening_type[i] == 0:
                    window_x1 = 0
                    window_x2 = 0
                    window_y2 = (zone_y-largura)/2
                    window_y1 = zone_y - window_y2
                    window_z1 = (zone_height-altura)/2
                    window_z2 = zone_height - window_z1

                else:
                    door_height = 2.1
                    largura = windowArea/door_height

                    if largura > zone_y:                        
                        largura = windowArea/altura
                        window_x1 = 0
                        window_x2 = 0
                        window_y2 = (zone_y-largura)/2
                        window_y1 = zone_y - window_y2
                        window_z1 = 0
                        window_z2 = altura
                    
                    else:
                        largura = windowArea/door_height
                        window_x1 = 0
                        window_x2 = 0
                        window_y2 = (zone_y-largura)/2
                        window_y1 = zone_y - window_y2
                        window_z1 = 0
                        window_z2 = door_height

                larguras_x1[i] = window_x1
                larguras_x2[i] = window_x2
                larguras_y1[i] = window_y1
                larguras_y2[i] = window_y2
                alturas_z1[i] = window_z1
                alturas_z2[i] = window_z2
            
            model["FenestrationSurface:Detailed"]["window_"+str(i)] = {
                "building_surface_name": "wall-"+str(i),
                "construction_name": "glass_construction",
                "number_of_vertices": 4.0,
                "surface_type": "Window",
                "vertex_1_x_coordinate": window_x1,
                "vertex_1_y_coordinate": window_y1,
                "vertex_1_z_coordinate": window_z2,
                "vertex_2_x_coordinate": window_x1,
                "vertex_2_y_coordinate": window_y1,
                "vertex_2_z_coordinate": window_z1,
                "vertex_3_x_coordinate": window_x2,
                "vertex_3_y_coordinate": window_y2,
                "vertex_3_z_coordinate": window_z1,
                "vertex_4_x_coordinate": window_x2,
                "vertex_4_y_coordinate": window_y2,
                "vertex_4_z_coordinate": window_z2
            }
    
    for obj in model['FenestrationSurface:Detailed']:
        model['FenestrationSurface:Detailed'][obj].update({
            "idf_max_extensible_fields": 0,
            "idf_max_fields": 22
        })
    
    #### SHADING -------------------------------------------------------

    # checks if there is shading in model
    for shade in shading:
        if shade > 0:
            model['Shading:Building:Detailed'] = {}
            
    if shading[0] > 0.01:

        if shading_type[0] == 0:
            z_shading = floor_height+zone_height
            x1_shading = 0
            x2_shading = zone_x
        else:
            z_shading = floor_height+alturas_z2[0]
            x1_shading = larguras_x1[0]
            x2_shading = larguras_x2[0]

        model['Shading:Building:Detailed']['shading_0'] = {
            "idf_max_extensible_fields": 12,
            "idf_max_fields": 15,
            'transmittance_schedule_name': '',
            'number_of_vertices': 4,
            "vertices": [
                {
                "vertex_x_coordinate": x1_shading,
                "vertex_y_coordinate": zone_y+shading[0],
                "vertex_z_coordinate": z_shading 
                },
                {
                "vertex_x_coordinate": x1_shading,
                "vertex_y_coordinate": zone_y,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": x2_shading,
                "vertex_y_coordinate": zone_y,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": x2_shading,
                "vertex_y_coordinate": zone_y+shading[0],
                "vertex_z_coordinate": z_shading
                }
            ]
        }
        
    if shading[1] > 0.01:

        if shading_type[1] == 0:
            z_shading = floor_height+zone_height
            y1_shading = zone_y
            y2_shading = 0
        else:
            z_shading = floor_height+alturas_z2[1]       
            y1_shading = larguras_y1[1]
            y2_shading = larguras_y2[1]

        model['Shading:Building:Detailed']['shading_1'] = {
            "idf_max_extensible_fields": 12,
            "idf_max_fields": 15,
            'transmittance_schedule_name': '',
            'number_of_vertices': 4,
            "vertices": [
                {
                "vertex_x_coordinate": zone_x+shading[1],
                "vertex_y_coordinate": y1_shading,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": zone_x,
                "vertex_y_coordinate": y1_shading,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": zone_x,
                "vertex_y_coordinate": y2_shading,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": zone_x+shading[1],
                "vertex_y_coordinate": y2_shading,
                "vertex_z_coordinate": z_shading
                }
            ]
        }
        
    if shading[2] > 0.01:

        if shading_type[2] == 0:
            z_shading = floor_height+zone_height
            x1_shading = zone_x
            x2_shading = 0

        else:
            z_shading = floor_height+alturas_z2[2]       
            x1_shading = larguras_x1[2]
            x2_shading = larguras_x2[2]       

        model['Shading:Building:Detailed']['shading_2'] = {
            "idf_max_extensible_fields": 12,
            "idf_max_fields": 15,
            'transmittance_schedule_name': '',
            'number_of_vertices': 4,
            "vertices": [
                {
                "vertex_x_coordinate": x1_shading,
                "vertex_y_coordinate": -shading[2],
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": x1_shading,
                "vertex_y_coordinate": 0,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": x2_shading,
                "vertex_y_coordinate": 0,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": x2_shading,
                "vertex_y_coordinate": -shading[2],
                "vertex_z_coordinate": z_shading
                }
            ]
        }
        
    if shading[3] > 0.01:

        if shading_type[3] == 0:
            z_shading = floor_height+zone_height
            y1_shading = 0
            y2_shading = zone_y
        
        else:
            z_shading = floor_height+alturas_z2[3]
            y1_shading = larguras_y1[3]
            y2_shading = larguras_y2[3]

        model['Shading:Building:Detailed']['shading_3'] = {
            "idf_max_extensible_fields": 12,
            "idf_max_fields": 15,
            'transmittance_schedule_name': '',
            'number_of_vertices': 4,
            "vertices": [
                {
                "vertex_x_coordinate": -shading[3],
                "vertex_y_coordinate": y1_shading,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": 0,
                "vertex_y_coordinate": y1_shading,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": 0,
                "vertex_y_coordinate": y2_shading,
                "vertex_z_coordinate": z_shading
                },
                {
                "vertex_x_coordinate": -shading[3],
                "vertex_y_coordinate": y2_shading,
                "vertex_z_coordinate": z_shading
                }
            ]
        }
         
    #### SURROUNDING SHADING -------------------------------------------------------

    # checks if there is surrouding shading in model
        
    if surrounding_shading[0] > 0.01:
        vertical_angle = surrounding_shading[0]
        surheight = math.tan(vertical_angle*(math.pi/180))*nearness
        surwidthleft = math.tan(surrounding_horizontal_left[0]*(math.pi/180))*nearness
        surwidthright = math.tan(surrounding_horizontal_right[0]*(math.pi/180))*nearness
        model['Shading:Building:Detailed']['surrounding_shading_0'] = \
        shadingjson(-surwidthleft, zone_y + nearness, surheight + floor_height,
                    -surwidthleft, zone_y + nearness, 0,
                    zone_x + surwidthright, zone_y + nearness, 0,
                    zone_x + surwidthright, zone_y + nearness, surheight + floor_height)
                
    if surrounding_shading[1] > 0.01:
        vertical_angle = surrounding_shading[1]
        surheight = math.tan(vertical_angle*(math.pi/180))*nearness
        surwidthleft = math.tan(surrounding_horizontal_left[1]*(math.pi/180))*nearness
        surwidthright = math.tan(surrounding_horizontal_right[1]*(math.pi/180))*nearness
        model['Shading:Building:Detailed']['surrounding_shading_1'] = \
        shadingjson(zone_x + nearness, zone_y + surwidthleft, surheight + floor_height,
                    zone_x + nearness, zone_y + surwidthleft, 0,
                    zone_x + nearness, -surwidthright, 0,
                    zone_x + nearness, -surwidthright, surheight + floor_height)
                
    if surrounding_shading[2] > 0.01:
        vertical_angle = surrounding_shading[2]
        surheight = math.tan(vertical_angle*(math.pi/180))*nearness
        surwidthleft = math.tan(surrounding_horizontal_left[2]*(math.pi/180))*nearness
        surwidthright = math.tan(surrounding_horizontal_right[2]*(math.pi/180))*nearness
        model['Shading:Building:Detailed']['surrounding_shading_2'] = \
        shadingjson(zone_x + surwidthleft, -nearness, surheight + floor_height,
                    zone_x + surwidthleft, -nearness, 0,
                    -surwidthright, -nearness, 0,
                    -surwidthright, -nearness, surheight + floor_height)
    
    if surrounding_shading[3] > 0.01:
        vertical_angle = surrounding_shading[3]
        surheight = math.tan(vertical_angle*(math.pi/180))*nearness
        surwidthleft = math.tan(surrounding_horizontal_left[3]*(math.pi/180))*nearness
        surwidthright = math.tan(surrounding_horizontal_right[3]*(math.pi/180))*nearness
        model['Shading:Building:Detailed']['surrounding_shading_3'] = \
        shadingjson(-nearness, -surwidthleft, surheight + floor_height,
                    -nearness, -surwidthleft, 0,
                    -nearness, zone_y + surwidthright, 0,
                    -nearness, zone_y + surwidthright, surheight + floor_height)


    #### VERTICAL SHADING -------------------------------------------------------

    ## north

    if shading_vertical_right[0] > 0.01:

        if shading_vertical_right_type[0] == 0:
            x_position = zone_x
            z1_position = floor_height
            z2_position = zone_height + floor_height            
        else:
            x_position = larguras_x1[0]
            z1_position = floor_height + alturas_z1[0]
            z2_position = floor_height + alturas_z2[0]

        vertical_right_len = math.tan(shading_vertical_right[0]*(math.pi/180))*zone_x
        model['Shading:Building:Detailed']['shading_vertical_right_0'] = \
        shadingjson(x_position, zone_y + vertical_right_len, z2_position,
                    x_position, zone_y + vertical_right_len, z1_position,
                    x_position, zone_y, z1_position,
                    x_position, zone_y, z2_position)

    if shading_vertical_left[0] > 0.01:

        if shading_vertical_left_type[0] == 0:
            x_position = 0
            z1_position = floor_height
            z2_position = zone_height + floor_height              
        else:
            x_position = larguras_x2[0]
            z1_position = floor_height + alturas_z1[0]
            z2_position = floor_height + alturas_z2[0]

        vertical_left_len = math.tan(shading_vertical_left[0]*(math.pi/180))*zone_x
        model['Shading:Building:Detailed']['shading_vertical_left_0'] = \
        shadingjson(x_position, zone_y, z2_position,
                    x_position, zone_y, z1_position,
                    x_position, zone_y + vertical_left_len, z1_position,
                    x_position, zone_y + vertical_left_len, z2_position)

    ## east

    if shading_vertical_right[1] > 0.01:
        
        if shading_vertical_right_type[1] == 0:
            y_position = 0
            z1_position = floor_height
            z2_position = zone_height + floor_height            
        else:
            y_position = larguras_y1[1]
            z1_position = floor_height + alturas_z1[1]
            z2_position = floor_height + alturas_z2[1]

        vertical_right_len = math.tan(shading_vertical_right[1]*(math.pi/180))*zone_y
        model['Shading:Building:Detailed']['shading_vertical_right_1'] = \
        shadingjson(zone_x + vertical_right_len, y_position, z2_position,
                    zone_x + vertical_right_len, y_position, z1_position,
                    zone_x, y_position, z1_position,
                    zone_x, y_position, z2_position)

    if shading_vertical_left[1] > 0.01:

        if shading_vertical_left_type[1] == 0:
            y_position = zone_y
            z1_position = floor_height
            z2_position = zone_height + floor_height              
        else:
            y_position = larguras_y2[1]
            z1_position = floor_height + alturas_z1[1]
            z2_position = floor_height + alturas_z2[1]

        vertical_left_len = math.tan(shading_vertical_left[1]*(math.pi/180))*zone_y
        model['Shading:Building:Detailed']['shading_vertical_left_1'] = \
        shadingjson(zone_x, y_position, z2_position,
                    zone_x, y_position, z1_position,
                    zone_x + vertical_left_len, y_position, z1_position,
                    zone_x + vertical_left_len, y_position, z2_position)

    ## south

    if shading_vertical_right[2] > 0.01:

        if shading_vertical_right_type[2] == 0:
            x_position = 0
            z1_position = floor_height
            z2_position = zone_height + floor_height            
        else:
            x_position = larguras_x1[2]
            z1_position = floor_height + alturas_z1[2]
            z2_position = floor_height + alturas_z2[2]

        vertical_right_len = math.tan(shading_vertical_right[2]*(math.pi/180))*zone_x
        model['Shading:Building:Detailed']['shading_vertical_right_2'] = \
        shadingjson(x_position, -vertical_right_len, z2_position,
                    x_position, -vertical_right_len, z1_position,
                    x_position, 0, z1_position,
                    x_position, 0, z2_position)

    if shading_vertical_left[2] > 0.01:

        if shading_vertical_left_type[2] == 0:
            x_position = zone_x
            z1_position = floor_height
            z2_position = zone_height + floor_height
        else:
            x_position = larguras_x2[2]
            z1_position = floor_height + alturas_z1[2]
            z2_position = floor_height + alturas_z2[2]            

        vertical_left_len = math.tan(shading_vertical_left[2]*(math.pi/180))*zone_x
        model['Shading:Building:Detailed']['shading_vertical_left_0'] = \
        shadingjson(x_position, 0, z2_position,
                    x_position, 0, z1_position,
                    x_position, -vertical_left_len, z1_position,
                    x_position, -vertical_left_len, z2_position)

    ## west

    if shading_vertical_right[3] > 0.01:

        if shading_vertical_right_type[3] == 0:
            y_position = zone_y
            z1_position = floor_height
            z2_position = zone_height + floor_height
        else:
            y_position = larguras_y1[3]
            z1_position = floor_height + alturas_z1[3]
            z2_position = floor_height + alturas_z2[3]             

        vertical_right_len = math.tan(shading_vertical_right[3]*(math.pi/180))*zone_y
        model['Shading:Building:Detailed']['shading_vertical_right_3'] = \
        shadingjson(-vertical_left_len, y_position, z2_position,
                    -vertical_left_len, y_position, z1_position,
                    0, y_position, z1_position,
                    0, y_position, z2_position)

    if shading_vertical_left[3] > 0.01:

        if shading_vertical_left_type[3] == 0:
            y_position = 0
            z1_position = floor_height
            z2_position = zone_height + floor_height
        else:
            y_position = larguras_y2[3]
            z1_position = floor_height + alturas_z1[3]
            z2_position = floor_height + alturas_z2[3]            

        vertical_left_len = math.tan(shading_vertical_left[3]*(math.pi/180))*zone_y
        model['Shading:Building:Detailed']['shading_vertical_left_3'] = \
        shadingjson(0, y_position, z2_position,
                    0, y_position, z1_position,
                    -vertical_left_len, y_position, z1_position,
                    -vertical_left_len, y_position, z2_position)                          

    #### THERMAL LOADS -------------------------------------------------

    if living_room:
        model["ElectricEquipment"]["equipment_loads"] = {
                "design_level": equipment,
                "design_level_calculation_method": "EquipmentLevel",
                "end_use_subcategory": "General",
                "fraction_latent": 0,
                "fraction_lost": 0,
                "fraction_radiant": 0.3,
                "idf_max_extensible_fields": 0,
                "idf_max_fields": 11,
                "schedule_name": "livingroom_equipment",
                "zone_or_zonelist_name": "room"
            }

    model["Lights"] = {
        "lights": {
            "watts_per_zone_floor_area": lights,
            "schedule_name": light_sch
        }
    }

    model["People"] = {
        "people": {
            "number_of_people": number_of_people,
            "number_of_people_schedule_name": occupation_sch,
            "activity_level_schedule_name": activity_sch
        }
    }

    #### MATERIALS -----------------------------------------------------


    model["WindowMaterial:SimpleGlazingSystem"] = {
        "glass_material": {
            "solar_heat_gain_coefficient": glass_fs
        }
    }

    #### AFN OBJECTS ---------------------------------------------------

    # AFN Simulation Control
    if bldg_ratio <= 1:  # x/y
        wind_azimuth = azimuth%180
    else:
        bldg_ratio = 1/bldg_ratio
        wind_azimuth = (azimuth+90)%180
        
    model["AirflowNetwork:SimulationControl"] = {
        "Ventilacao": {
            "azimuth_angle_of_long_axis_of_building": wind_azimuth,
            "ratio_of_building_width_along_short_axis_to_width_along_long_axis": bldg_ratio
        }
    }

    # AFN Surface

    if bound == 'hive':        
        model["AirflowNetwork:MultiZone:ExternalNode"] = hive_externalnodes
        model["AirflowNetwork:MultiZone:Surface"] = hive_elas

    else:
        model["AirflowNetwork:MultiZone:ExternalNode"] = {}
        model["AirflowNetwork:MultiZone:Surface"] = {}

    for i in range(4):
        if wwr[i] > 0:
            model["AirflowNetwork:MultiZone:Surface"]["AirflowNetwork:MultiZone:Surface "+str(i)] = {
                "external_node_name": "window_"+str(i)+"_Node",
                "indoor_and_outdoor_enthalpy_difference_upper_limit_for_minimum_venting_open_factor": 300000.0,
                "indoor_and_outdoor_temperature_difference_upper_limit_for_minimum_venting_open_factor": 100.0,
                "leakage_component_name": "detailed_window",
                "surface_name": "window_"+str(i),
                "ventilation_control_mode": "Temperature",
                "ventilation_control_zone_temperature_setpoint_schedule_name": "Temp_setpoint",
                "venting_availability_schedule_name": "VN",  # occupation_sch,
                "window_door_opening_factor_or_crack_factor": open_fac[i]
            }
            
            model["AirflowNetwork:MultiZone:ExternalNode"]["window_"+str(i)+"_Node"] = {
                "idf_max_extensible_fields": 0,
                "idf_max_fields": 5,
                "symmetric_wind_pressure_coefficient_curve": "No",
                "wind_angle_type": "Absolute",
                "wind_pressure_coefficient_curve_name": "side_"+str(i)+"_coef"
            }
    
    for obj in model["AirflowNetwork:MultiZone:Surface"]:
        
        model["AirflowNetwork:MultiZone:Surface"][obj].update({
            "idf_max_extensible_fields": 0,
            "idf_max_fields": 12
        })
        
    model["AirflowNetwork:MultiZone:Surface"]["AirflowNetwork:MultiZone:Surface Door"] = {
            "external_node_name": "",
            "indoor_and_outdoor_enthalpy_difference_upper_limit_for_minimum_venting_open_factor": 300000.0,
            "indoor_and_outdoor_temperature_difference_upper_limit_for_minimum_venting_open_factor": 100.0,
            "leakage_component_name": "ela",
            "surface_name": "",
            "ventilation_control_mode": "NoVent",
            "window_door_opening_factor_or_crack_factor": 1.0,
            "idf_max_extensible_fields": 0,
            "idf_max_fields": 12
        }

    window_areas = []
    
    for i in range(4):
        if i%2 == 0:
            window_areas.append(wwr[i] * open_fac[i] * zone_x)
        else:
            window_areas.append(wwr[i] * open_fac[i] * zone_y)
        
        if exp[i] == 0:
            model["AirflowNetwork:MultiZone:Surface"]["AirflowNetwork:MultiZone:Surface Door"]["surface_name"] = "wall-{}".format(i)
            if bound != 'hive':
                model["AirflowNetwork:MultiZone:ExternalNode"]["door_Node"] = { 
                "idf_max_extensible_fields": 0,
                "idf_max_fields": 5,
                "symmetric_wind_pressure_coefficient_curve": "No",
                "wind_angle_type": "Absolute",
                "wind_pressure_coefficient_curve_name": "side_{}_coef".format(i)
                }

    for i in model["AirflowNetwork:MultiZone:ExternalNode"]:
        model["AirflowNetwork:MultiZone:ExternalNode"][i]['external_node_height'] = floor_height*zone_height + zone_height/2

    if bound == 'hive':
        model["AirflowNetwork:MultiZone:WindPressureCoefficientValues"] = cp_calc(bldg_ratio, azimuth=azimuth, window_areas=window_areas, cp_eq=False)
    else:     
        elasinglesurfacename = model["AirflowNetwork:MultiZone:Surface"]["AirflowNetwork:MultiZone:Surface Door"]["surface_name"]
        model["BuildingSurface:Detailed"][elasinglesurfacename]["outside_boundary_condition"] = "Outdoors"
        model["AirflowNetwork:MultiZone:Surface"]["AirflowNetwork:MultiZone:Surface Door"]["external_node_name"] = "door_Node"
        model["AirflowNetwork:MultiZone:WindPressureCoefficientValues"] = cp_calc(bldg_ratio, azimuth=azimuth, window_areas=window_areas, cp_eq=True)

    #### DEFINING CONSTRUCTION AND MATERIALS ---------------------------
        
    if len(construction) > 0:
        with open(construction, 'r') as file:
            construction_wall = json.loads(file.read())
        update(model, construction_wall)
    else:
        construction_wall = concrete_wall(wall_u, wall_ct, absorptance)
        update(model, construction_wall)
        
    #### EMS PROGRAM ---------------------------------------------------
    
    model["EnergyManagementSystem:Program"] = {}
    
    with open(EMS_PROGRAM_FILE, 'r') as file:
        ems_program = json.loads(file.read())

    if living_room:
        model["EnergyManagementSystem:Program"]["ems_program"] = ems_program["living_room"]
    else:
        model["EnergyManagementSystem:Program"]["ems_program"] = ems_program["bedroom"]

    #### BRING SEED TO MODEL -------------------------------------------

    with open(input_file, 'r') as file:
        seed = json.loads(file.read())

    # update(model, seed)
    complete_model = update(seed, model)
    
    with open(output, 'w') as file:
        file.write(json.dumps(complete_model))
    
    #### CONVERT TO IDF ------------------------------------------------
    
    if convert:
        os.system('energyplus -x -c '+output)
        if os.name == 'posix':
            os.system('rm eplusout*')
            os.system('rm sqlite.err')
        else:
            os.system('del eplusout*')
            os.system('del sqlite.err')

main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0, absorptance=.5,
    wall_u=4.083, wall_ct=165.6, ground=1, roof=1, shading=[0,1,1,0], shading_type=[0,1,0,0], surrounding_shading = [0,40,50,45],
    nearness = 10, surrounding_horizontal_left = [0,10,20,30], surrounding_horizontal_right = [0,10,15,5],
    shading_vertical_left = [0,10,10,10], shading_vertical_right = [0,6,6,6],
    shading_vertical_left_type = [0,1,0,1], shading_vertical_right_type = [0,1,0,1],
    living_room = False, exp=[0,1,1,1], wwr=[0,.75,.2,.4], opening_type=[0,1,0,1], open_fac=[0,.3,0.5,0.7],
    glass_fs=.87, equipment=0, lights = 5, bldg_ratio=0.85, floor_height=10, ela_area = 0.7, equipment_hive = 100, bound='hive',
    input_file='seed.json' , output='simula/hive_12-04_floor1_roof1.epJSON',
    construction='construction_tijolomacico_double.json', convert=False)  #   3.87 x 5.54 

'''    
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=1, roof=0, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=0, door=True, bound='hive',
    input_file='seed.json' , output='simula\hive_12-04_floor1_roof0.epJSON')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=0, roof=1, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=0, door=True, bound='hive',
    input_file='seed.json' , output='simula\hive_12-04_floor0_roof1.epJSON')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=0, roof=0, shading=[1,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=3, door=True, bound='hive',
    input_file='seed.json' , output='simula\hive_12-04_floor0_roof0.epJSON')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=1, roof=1, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=3, door=True, bound='hive',
    input_file='seed.json' , output='simula\hive_12-04_pilotis.epJSON')  #   3.87 x 5.54 
 
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=1, roof=1, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=0, door=True, bound='double',
    input_file='seed.json' , output='simula\double_12-04_floor1_roof1.epJSON', construction='construction_tijolomacico_double.json')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=1, roof=0, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=0, door=True, bound='double',
    input_file='seed.json' , output='simula\double_12-04_floor1_roof0.epJSON', construction='construction_tijolomacico_double.json')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=0, roof=1, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=0, door=True, bound='double',
    input_file='seed.json' , output='simula\double_12-04_floor0_roof1.epJSON', construction='construction_tijolomacico_double.json')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=0, roof=0, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=3, door=True, bound='double',
    input_file='seed.json' , output='simula\double_12-04_floor0_roof0.epJSON', construction='construction_tijolomacico_double.json')  #   3.87 x 5.54 
   
main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=0,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=1, roof=1, shading=[0,0,0,0], living_room = True,
    exp=[1,0,0,0], wwr=[0.0866425992,0,0,0], open_fac=[.45,0,0,0], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=3, door=True, bound='double',
    input_file='seed.json' , output='simula\double_12-04_pilotis.epJSON', construction='construction_tijolomacico_double.json')  #   3.87 x 5.54 

### old   
main(exp=[0,0,0,0], shading=[0,0,0,0], wwr=[0,0,0,0], open_fac=[0,0,0,0], output= "hive_test.epJSON")  # (input_file='seed_single_U-conc-eps.json')
main(exp=[1,1,1,1], shading=[0,0,0,0], wwr=[1,0,0,0], open_fac=[.5,0,0,0], output= "ela_test.epJSON")  # (input_file='seed_single_U-conc-eps.json')

main(zone_area=21.4398, zone_ratio=0.6985559566, zone_height=2.5, azimuth=270,
    absorptance=.5, wall_u=4.083, wall_ct=165.6,
    ground=1, roof=1, shading=[.5,0,0,0.5], living_room = True,
    exp=[1,0,0,1], wwr=[0.0866425992,0,0,0.15503875], open_fac=[.45,0,0,.45], glass_fs=.87, 
    bldg_ratio=0.85, floor_height=0, door=True, bound='hive',
    input_file='seed.json' , output='simula\test.epJSON')  #   3.87 x 5.54 
''' 
