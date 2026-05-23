#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# detect and process complex polygons. complex polygons are polygons with edge shared same polygon with two sides

import modo
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import (
    drop_selection,
    set_selection_mode,
    execution_time_alarm,
    select_polygons,
    select_if_exists,
    remove_if_exist,
    )

from h3d_slice_complex_polygons.scripts.complex_polygons_tools import (
    ITEM_SEL,
    POLYGON_SEL,
    get_complex_polygons,
    get_shadow_vertex_pairs,
    slice_by_vertex_pair,
    get_containing_meshes,
    )

from h3d_utilites.scripts.h3d_debug import (
    h3dd,
    execution_time,
    )


@execution_time
@execution_time_alarm
def main():
    meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)
    if not meshes:
        print('No meshes selected')
        return

    complex_polygons_by_mesh: dict[modo.Mesh, list[modo.MeshPolygon]] = {}
    for mesh in meshes:
        polygons = get_complex_polygons(mesh)
        complex_polygons_by_mesh[mesh] = polygons

    unsuccessful_polygons: list[modo.MeshPolygon] = []
    tmp_items: set[modo.Item] = set()
    for polygons in complex_polygons_by_mesh.values():
        for polygon in polygons:
            shadow_vertex_pairs, tmp_loc = get_shadow_vertex_pairs(polygon)
            tmp_items.add(tmp_loc)
            for shadow_vertex_pair in shadow_vertex_pairs:
                is_successful = slice_by_vertex_pair(shadow_vertex_pair)
                if is_successful:
                    break
            else:
                unsuccessful_polygons.append(polygon)

    for tmp_item in tmp_items:
        remove_if_exist(tmp_item, children=True)

    drop_selection(ITEM_SEL)
    select_if_exists(get_containing_meshes(unsuccessful_polygons))
    drop_selection(POLYGON_SEL)
    set_selection_mode(POLYGON_SEL)
    select_polygons(unsuccessful_polygons)


if __name__ == '__main__':
    h3dd.enable_debug_output(True)
    main()
