import numpy as np
import trimesh
import pyvista as pv
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap as lsc

# nacitanie meshu
def load_mesh(path):
    mesh = trimesh.load(path, force="mesh")
    mesh.merge_vertices()   # zlucoavnie vrcholov je nutne pre vypocet krivosti, inak by boli vsetky trojuholniky brane ako ostrovy
    return mesh

# normalizacia meshu
def normalize_mesh(mesh):
    vertices = mesh.vertices
    
    # transformacia na povodny
    centroid = vertices.mean(axis=0)
    vertices -= centroid

    # normalizacia velkosti
    scale = np.max(np.linalg.norm(vertices, axis=1))
    if scale>0:
        vertices /= scale

    mesh.vertices = vertices
    return mesh

# vypocet plohy vrcholov pre vahy histogramu
def compute_vertex_areas(mesh):
    # ziskame vsetky trojuholniky z meshu
    face_areas = mesh.area_faces
    vertex_areas = np.zeros(len(mesh.vertices))

    # kazdemu vrcholu pridame vahu trojuholnika/3
    np.add.at(vertex_areas, mesh.faces[:, 0], face_areas/3.0)   # rychlejsie by bolo nasobit 0.3
    np.add.at(vertex_areas, mesh.faces[:, 1], face_areas/3.0)
    np.add.at(vertex_areas, mesh.faces[:, 2], face_areas/3.0)

    return vertex_areas

# vypocet krivosti k1, k2
def compute_curvatures(mesh):
    pv_faces = np.column_stack((np.full(len(mesh.faces), 3), mesh.faces)).flatten()  # transformacia meshu pre vstup do pyVista, jeden dlhy linearny zoznam
    #pv_mesh = pv.PolyData(mesh.vertices, np.hstack((np.full((len(mesh.faces),1),3), mesh.faces)).astype(np.int64))
    pv_mesh = pv.PolyData(mesh.vertices, pv_faces)
    k1 = pv_mesh.curvature(curv_type="maximum")
    k2 = pv_mesh.curvature(curv_type="minimum")

    return np.array(k1), np.array(k2)


def compute_curvatures_voronoi(mesh, vertex_areas):
    # plocha prisluchajuca vrcholom
    vertex_areas[vertex_areas < 1e-12] = 1e-12  # osetrenie nulovej plochy

    #gaussova krivost K (uhlovy deficit)
    angles_sum = mesh.vertex_defects
    K = angles_sum/vertex_areas

    radius = np.mean(mesh.edges_unique_length)

    #stredna krivost H (integrovana stredna krivost)
    H_integrated = trimesh.curvature.discrete_mean_curvature_measure(mesh, mesh.vertices, radius)
    H = H_integrated / vertex_areas

    # vypocet hlavnych krivosti
    discriminant = H**2 - K
    discriminant[discriminant < 0] = 0
    k1 = H + np.sqrt(discriminant)
    k2 = H - np.sqrt(discriminant)

    return k1, k2

# vypocet shape index
def compute_shape_index(k1, k2):
    # shape_index = ((2/np.pi) * np.arctan((k1+k2) / (k1-k2 + 1e-8)))
    denom = k1-k2
    denom[np.abs(denom) < 1e-10] = 1e-10    # osetrenie delenia nulou
    
    shape_index = ((1/2) - ((1/np.pi) * (np.arctan((k1+k2) / denom))))
    return shape_index
    

def compute_ssd_histogram(shape_index, vertex_areas):
    # hist, bins = np.histogram(shape_index, bins=90, range=(0.01,0.99), weights=vertex_areas, density=True)
    hist, bins = np.histogram(shape_index, bins=90, range=(0,1), weights=vertex_areas, density=False)

    total_area = np.sum(hist)
    if total_area > 0:
        hist = hist/total_area
    
    return hist, bins

# vypocet euklidovskej vzdialenosti
def euklid_distance(hist1, hist2):
    d = np.linalg.norm(hist1 - hist2)   # alternativa d = np.sqrt(np.sum((hist1 - hist2)**2))
    return d


if __name__ == "__main__":
    # spracovanie modelu1
    mesh = load_mesh("cesta k modelu")
    mesh = normalize_mesh(mesh)
    vertex_areas = compute_vertex_areas(mesh)
    k1,k2 = compute_curvatures(mesh)
    shape_index = compute_shape_index(k1, k2)
    hist, bins = compute_ssd_histogram(shape_index, vertex_areas)

    # spracovanie modelu2
    mesh2 = load_mesh("cesta k modelu2")
    mesh2 = normalize_mesh(mesh2)
    vertex_areas2 = compute_vertex_areas(mesh2)
    k12,k22 = compute_curvatures(mesh2)
    shape_index2 = compute_shape_index(k12,k22)
    hist2, bins2 = compute_ssd_histogram(shape_index2, vertex_areas2)

    # pocitanie euklidovskej vzdialenosti medzi ziskanymi histogramami
    euklidD = euklid_distance(hist, hist2)
    print(f"Euklidovska vzdialenost: {euklidD}")
    
    # vizualizacia histogramu modelu 1
    cmap =  lsc.from_list(
        "custom", [(0.0, "lime"), (0.5, "turquoise"), (1.0, "blue")]
    )
    bin_center = (bins[:-1] + bins[1:]) / 2
    norm = (bin_center - 0) / (1-0)

    colors = cmap(norm)

    # fontsize je nastaveny z dovodu prehladnejsej verzie grafov do BP, da sa to odstranit a neprist o ziadnu informaciu
    plt.bar(bins[:-1], hist, width=bins[1]-bins[0], color=colors)
    plt.xlabel("Shape Index", fontsize=38)
    plt.ylabel("Frequency", fontsize=38)
    plt.title("3D SSD kozmetika3", fontsize=45)

    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    plt.tight_layout()
    plt.show()