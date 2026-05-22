import bpy
import bmesh
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Base cutter",
    "author": "Radoslav Dujava",
    "version": (1.0),
    "blender": (4.5),
    "location": "View3D > Sidebar (N) > Base cutter",
    "description": "Removes the bottom side of the selected 3D mesh and export new .obj file",
    "cathegory": "Object",
}

class Object_ot_cut_and_export(bpy.types.Operator, ExportHelper):
    """Cuts the bottom side of mesh and export created model"""
    bl_idname = "object.cut_and_export"
    bl_label = "Cut and export (obj)"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".obj"
    filter_glob: bpy.props.StringProperty(
        default="*.obj",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    cut_height: bpy.props.FloatProperty(
        name="Height of the cut (Z)",
        description="How high the cut should be",
        default=0.1,
        min=0.001
    )

    fill_hole: bpy.props.BoolProperty(
        name="Fill the hole"
        description="Creates a new face after a cut"
        default=True
    )
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "You have to select MESH object")
            return {'CANCELLED'}
        
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        
        min_z = min([v.co.z for v in bm.verts])
        
        cutoff_z = min_z + self.cut_height
        
        verts_to_delete = [v for v in bm.verts if v.co.z <= cutoff_z]

        bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
        
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.ops.wm.obj_export(
            filepath=self.filepath,
            export_selected_objects=True
        )
        
        self.report({'INFO'}, f"model was updated succesfully and saved to: {self.filepath}")
        
        return {'FINISHED'}
    
    
class VIEW3D_pt_base_cutter(bpy.types.Panel):
    """Panel in the side menu"""
    bl_label = "Base cutter"
    bl_idname = "VIEW3D_pt_base_butter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Base cutter"
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Cut settings:")
        
        layout.operator("object.cut_and_export")
        
        
def register():
    bpy.utils.register_class(Object_ot_cut_and_export)
    bpy.utils.register_class(VIEW3D_pt_base_cutter)
    
def unregister():
    bpy.utils.unregister_class(Object_ot_cut_and_export)
    bpy.utils.unregister_class(VIEW3D_pt_base_cutter)
    
if __name__ == "__main__":
    register()