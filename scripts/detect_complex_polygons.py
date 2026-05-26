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
    # select_polygons,
    # select_if_exists,
    remove_if_exist,
    )

from h3d_slice_complex_polygons.scripts.complex_polygons_tools import (
    ITEM_SEL,
    POLYGON_SEL,
    get_complex_polygons,
    get_shadow_vertex_pairs,
    slice_by_vertex_pair,
    build_vertex_world_coords,
    # get_containing_meshes,
    )

from h3d_utilites.scripts.h3d_debug import (
    h3dd,
    execution_time,
    # prints,
    )


@execution_time
@execution_time_alarm
def main():
    meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)
    if not meshes:
        print('No meshes selected')
        return

    for mesh in meshes:
        original_coords = build_vertex_world_coords(mesh)
        while polygons := get_complex_polygons(mesh):
            for polygon in polygons:
                # prints(polygon)
                # TODO exclude aready connected edge loops
                shadow_vertex_pairs, shadow_coords, tmp_loc = get_shadow_vertex_pairs(polygon)

                slice_by_vertex_pair(polygon, original_coords, shadow_vertex_pairs[0], shadow_coords)

                remove_if_exist(tmp_loc, children=True)

    drop_selection(ITEM_SEL)
    drop_selection(POLYGON_SEL)
    set_selection_mode(POLYGON_SEL)


if __name__ == '__main__':
    h3dd.enable_debug_output(True)
    main()
