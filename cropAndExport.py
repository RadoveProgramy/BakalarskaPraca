import bpy
import bmesh
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Selection crop & Export",
    "author": "Radoslav Dujava",
    "version": (2, 0),
    "blender": (4, 5),
    "location": "View3D > Sidebar (N) > Mesh Cropper",
    "description": "Ponechá len označenú časť meshu a vyexportuje nový .obj súbor",
    "category": "Object",
}

class OBJECT_OT_cropAndExport(bpy.types.Operator, ExportHelper):
    """Ponechá len označenú časť meshu a exportuje"""
    bl_idname = "object.crop_and_export"
    bl_label = "Orezať výber a Exportovať"
    bl_options = {'REGISTER','UNDO'}
    
    filename_ext = ".obj"
    filter_glob: bpy.props.StringProperty(
        default="*.obj",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Musíš mať aktívny Mesh objekt!")
            return {'CANCELLED'}
        
        if context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Pre orezanie musíš byť v Edit móde a označiť časť, ktorú chceš zachovať!")
            return {'CANCELLED'}
        
        bm = bmesh.from_edit_mesh(obj.data)
        
        vertsToDelete = [v for v in bm.verts if not v.select]
        
        if len(vertsToDelete) == len(bm.verts):
            self.report({'WARNING'}, "Nemáš označené nič Označ časť, ktorú chceš ponechať.")
            return {'CANCELLED'}
        
        bmesh.ops.delete(bm, geom=vertsToDelete, context='VERTS')
        
        boundary_edges = [e for e in bm.edges if e.is_boundary]

        if boundary_edges:
            bmesh.ops.holes_fill(bm, edges=boundary_edges, sides=0)
            bmesh.ops.triangulate(bm, faces=bm.faces)
        
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        try:
            bpy.ops.wm.obj_export(
                filepath=self.filepath,
                export_selected_objects=True
            )
        except AttributeError:
            bpy.ops.export_scene.obj(
                filepath=self.filepath,
                use_selection=True
            )
        
        self.report({'INFO'}, "Model bol úspešne orezaný.")
        return {'FINISHED'}
   
class VIEW3D_PT_meshCropper(bpy.types.Panel):
    """Panel v N-menu"""
    bl_label = "Mesh Cropper"
    bl_idname = "VIEW3D_PT_meshCropper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cropper"
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.label(text="Postup:")
        col.label(text="1. Prejdi do Edit módu (TAB)")
        col.label(text="2. Označ časť, ktorú chceš ZACHOVAŤ")
        col.separator()
        
        col.operator("object.crop_and_export", icon='MESH_DATA')
        
def register():
    bpy.utils.register_class(OBJECT_OT_cropAndExport)
    bpy.utils.register_class(VIEW3D_PT_meshCropper)
    
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_cropAndExport)
    bpy.utils.unregister_class(VIEW3D_PT_meshCropper)
        
if __name__ == '__main__':
    register()