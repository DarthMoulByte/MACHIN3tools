bl_info = {
    "name": "Cleans Up Good",
    "author": "MACHIN3",
    "version": (0, 1),
    "blender": (2, 77, 0),
    "location": "Spacebar Menu/Hotkey 3",
    "description": "Removes doubles, dissolves degenerates, deletes loose vertices and edges, recalculates normals, dissolves 2-edged vertices, selects non-manifold geometry. Works in edit mode and object mode(incl. on multiple objects).",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh"}


# SETTINGS
button = "THREE"
press = "PRESS"
alt = False
shift = False
ctrl = False

objectmodeshortcut = False  # set to True, if the keyboard shortcut(assigned above) should work in OBJECT mode as well, otherwise it's just EDIT mode. Call the script from the spacebar menu in object mode in that case.
auto2edged = True  # set to False, if 2 edged vertices should not be removed on each clean up run. It can always be called separately from the spacebar menu. You might want to disable this if you are working with meshes above 50k triangles, if the clean up delay bothers you.


import bpy


class CleansUpGood(bpy.types.Operator):
    bl_idname = "machin3.clean_up"
    bl_label = "MACHIN3: Cleans Up Good"

    def execute(self, context):
        # get object mode
        mode = self.get_mode()

        if mode == "OBJECT":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    print(obj.name)
                    bpy.context.scene.objects.active = obj
                    bpy.ops.object.mode_set(mode='EDIT')
                    compmode = self.get_comp_mode()
                    self.clean_up(compmode)
                    bpy.ops.object.mode_set(mode='OBJECT')
        elif mode in ["VERT", "EDGE", "FACE"]:
            self.clean_up(mode)

        return {'FINISHED'}

    def clean_up(self, mode):  # needs to be in edit mode
        # remove doubles
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()

        # dissolve degenerates
        bpy.ops.mesh.dissolve_degenerate()

        # recalculate normals
        bpy.ops.mesh.normals_make_consistent(inside=False)

        # delete loose geometry (except faces)
        bpy.ops.mesh.delete_loose(use_faces=False)
        bpy.ops.mesh.select_all(action='DESELECT')

        # dissolve two-edged vertices, will go into vertex mode
        if auto2edged:
            bpy.ops.machin3.remove_2_edged_verts()

        # select non-manifold geometry, helpful to find holes
        # also helpful for finding overlapping bevels too and rarely invisible/undetectable vertices, both of which can prevent booleans to work
        bpy.ops.mesh.select_non_manifold()  # will work in either vert or edge mode, but not in face mode

        # go back into the original mode
        if mode == "EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        elif mode == "FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')

    def get_mode(self):
        objmode = bpy.context.active_object.mode

        if objmode == "OBJECT":
            # print("object mode")
            return "OBJECT"
        elif objmode == "EDIT":
            return self.get_comp_mode()

    def get_comp_mode(self):
        subobjtuple = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
        if subobjtuple == (True, False, False):
            # print("edit mode: vertex")
            return "VERT"
        elif subobjtuple == (False, True, False):
            # print("edit mode: edge")
            return "EDGE"
        elif subobjtuple == (False, False, True):
            # print("edit mode: face")
            return "FACE"
        else:
            # print("Unsupported multi sub-object mode")
            return None


class Remove2EdgedVerts(bpy.types.Operator):
    bl_idname = "machin3.remove_2_edged_verts"
    bl_label = "MACHIN3: Remove 2-edged Vertices"

    def execute(self, context):
        self.remove_2_edged_verts()

        return {'FINISHED'}

    def remove_2_edged_verts(self):
        mesh = bpy.context.object.data

        # get vertex count
        bpy.ops.object.mode_set(mode='OBJECT')
        count = len(mesh.vertices)

        # select first edge
        mesh.edges[0].select = True
        bpy.ops.object.mode_set(mode='EDIT')

        # create 2-edged vert
        bpy.ops.mesh.subdivide(smoothness=0)
        bpy.ops.mesh.select_all(action='DESELECT')

        # select newest vert
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh.vertices[-1].select = True
        bpy.ops.object.mode_set(mode='EDIT')

        # select similar
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_similar(type='EDGE', threshold=0.01)

        # limited dissolve
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.select_all(action='DESELECT')

        # fetch new vertex count
        bpy.ops.object.mode_set(mode='OBJECT')
        newcount = len(mesh.vertices)
        bpy.ops.object.mode_set(mode='EDIT')

        print("Info: Removed: %d two-edged vertices" % (count - newcount))


def register():
    bpy.utils.register_class(CleansUpGood)
    bpy.utils.register_class(Remove2EdgedVerts)

    wm = bpy.context.window_manager

    if objectmodeshortcut:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    else:
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')

    kmi = km.keymap_items.new(CleansUpGood.bl_idname, button, press, alt=alt, shift=shift, ctrl=ctrl)


def unregister():
    bpy.utils.unregister_class(CleansUpGood)
    bpy.utils.unregister_class(Remove2EdgedVerts)


if __name__ == "__main__":
    register()
