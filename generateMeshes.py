
# Units are mm, kg, s
import parameters as params

def generateMeshes(modelling):
    """
    Generates the volume mesh of the body
    """

    # We load the meshes, the body surface and cavities wall
    meshbody = modelling.addObject("MeshSTLLoader", name="meshbody", filename="mesh/body.stl")
    bodycavityMesh = "mesh/bodycavity_sphere.stl" if params.bc_cavity == "sphere" else "mesh/bodycavity_accordion.stl"
    meshbodycavity = modelling.addObject("MeshSTLLoader", name="meshbodycavity", filename=bodycavityMesh, rotation=params.bc_rotation, scale3d=params.bc_scale, translation=params.bc_translation)
    meshheadcavity1 = modelling.addObject("MeshSTLLoader", name="meshheadcavity1", filename="mesh/headcavity.stl", rotation=params.nc_rotation, scale3d=params.nc_scale, translation=params.nc_translation[0])
    meshheadcavity2 = modelling.addObject("MeshSTLLoader", name="meshheadcavity2", filename="mesh/headcavity.stl", rotation=params.nc_rotation, scale3d=params.nc_scale, translation=params.nc_translation[1])
    meshheadcavity3 = modelling.addObject("MeshSTLLoader", name="meshheadcavity3", filename="mesh/headcavity.stl", rotation=params.nc_rotation, scale3d=params.nc_scale, translation=params.nc_translation[2])

    # We create a node for each part
    bodysurface = modelling.addChild("BodySurface")
    bodysurface.addObject("MeshTopology", src=meshbody.linkpath)

    bodycavity = modelling.addChild("BodyCavity")
    bodycavity.addObject("MeshTopology", src=meshbodycavity.linkpath)

    for i in range(3):
        headcavity = modelling.addChild("HeadCavity" + str(i + 1))
        headcavity.addObject("MeshTopology",
                             src=[meshheadcavity1,
                                  meshheadcavity2,
                                  meshheadcavity3][i].linkpath)

    # We compute the difference between the body and the first cavity
    meshbodydifference = modelling.addChild("MeshBodyDifference")
    meshbodydifference.addObject("BooleanOperations", name="operation0", operation="difference",
                                 position1=meshbody.position.linkpath,
                                 triangles1=meshbody.triangles.linkpath,
                                 position2=meshbodycavity.position.linkpath,
                                 triangles2=meshbodycavity.triangles.linkpath
                                 )

    # We continue with the difference between the result and the next cavity
    for i in range(3):
        meshbodydifference.addObject("BooleanOperations", name="operation" + str(i + 1), operation="difference",
                                     position1="@operation" + str(i) + ".outputPosition",
                                     triangles1="@operation" + str(i) + ".outputTriangles",
                                     position2=[meshheadcavity1,
                                                meshheadcavity2,
                                                meshheadcavity3][i].position.linkpath,
                                     triangles2=[meshheadcavity1,
                                                 meshheadcavity2,
                                                 meshheadcavity3][i].triangles.linkpath
                                     )
    meshbodydifference.addObject("MeshTopology",
                                 position="@operation3.outputPosition",
                                 triangles="@operation3.outputTriangles")

    # Once we have the mesh of the body cut of its cavities, we generate the volume mesh
    bodyvolume = modelling.addChild("BodyVolume")
    bodyvolume.addObject("MeshGenerationFromPolyhedron",
                         inputPoints=meshbodydifference.MeshTopology.position.linkpath,
                         inputTriangles=meshbodydifference.MeshTopology.triangles.linkpath,
                         drawTetras=True,
                         facetSize=15,
                         facetApproximation=4 if params.COARSE else 2,
                         cellRatio=2,
                         cellSize=15,
                         facetAngle=30)
    bodyvolume.addObject("MeshTopology", name="topology",
                         position="@MeshGenerationFromPolyhedron.outputPoints",
                         tetrahedra="@MeshGenerationFromPolyhedron.outputTetras")

    # We export the generated mesh
    typeName = "coarse" if params.COARSE else "fine"
    bodyvolume.addObject("VTKExporter", filename="mesh/body_"+params.bc_cavity+"_"+typeName,
                         position=bodyvolume.topology.position.linkpath,
                         edges=False, tetras=True, hexas=True,
                         exportAtEnd=True)

    return bodyvolume


def createScene(rootnode):
    from header import addHeader

    settings, modelling, simulation = addHeader(rootnode)

    settings.addObject("RequiredPlugin", name="CGALPlugin")
    settings.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')  # Needed to use components [MeshSTLLoader]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Constant')  # Needed to use components [MeshTopology]
    settings.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')  # Needed to use components [OglModel]

    rootnode.VisualStyle.displayFlags=["showVisual", "showBehaviorModels"]
    rootnode.gravity.value = [0, 0, -9810]

    generateMeshes(modelling)
