
def generateMeshes(modelling):
    """
    Generates the volume mesh of the body
    """
    meshbody = modelling.addObject("MeshSTLLoader", name="meshbody", filename="mesh/body.stl")
    meshbodycavity = modelling.addObject("MeshSTLLoader", name="meshbodycavity", filename="mesh/bodycavity.stl")
    meshheadcavity1 = modelling.addObject("MeshSTLLoader", name="meshheadcavity1", filename="mesh/headcavity1.stl")
    meshheadcavity2 = modelling.addObject("MeshSTLLoader", name="meshheadcavity2", filename="mesh/headcavity2.stl")
    meshheadcavity3 = modelling.addObject("MeshSTLLoader", name="meshheadcavity3", filename="mesh/headcavity3.stl")

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

    meshbodydifference = modelling.addChild("MeshBodyDifference")
    meshbodydifference.addObject("BooleanOperations", name="operation0", operation="difference",
                                 position1=meshbody.position.linkpath,
                                 triangles1=meshbody.triangles.linkpath,
                                 position2=meshbodycavity.position.linkpath,
                                 triangles2=meshbodycavity.triangles.linkpath
                                 )
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
    meshbodydifference.addObject("OglModel")

    bodyvolume = modelling.addChild("BodyVolume")
    bodyvolume.addObject("MeshGenerationFromPolyhedron",
                         inputPoints=meshbodydifference.MeshTopology.position.linkpath,
                         inputTriangles=meshbodydifference.MeshTopology.triangles.linkpath,
                         drawTetras=False,
                         facetSize=15,
                         facetApproximation=9,
                         cellRatio=2,
                         cellSize=15,
                         facetAngle=30)
    bodyvolume.addObject("MeshTopology",
                         position="@MeshGenerationFromPolyhedron.outputPoints",
                         tetrahedra="@MeshGenerationFromPolyhedron.outputTetras")

    # TODO : export the generated meshes

    return bodyvolume


def createScene(rootnode):
    from header import addHeader, addSolvers
    from scene import addRobot
    from splib3.animation import AnimationManager, animate

    rootnode.addObject(AnimationManager(rootnode))
    settings, modelling, simulation = addHeader(rootnode)

    settings.addObject("RequiredPlugin", name="CGALPlugin")
    settings.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')  # Needed to use components [MeshSTLLoader]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Constant')  # Needed to use components [MeshTopology]
    settings.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')  # Needed to use components [OglModel]

    rootnode.addObject("VisualStyle", displayFlags=["hideWireframe", "hideVisual", "showBehaviorModels", "showForceFields"])
    rootnode.gravity.value = [0, -9810, 0]
    # rootnode.addObject("ClipPlane", position=[250, 0, 0])

    generateMeshes(modelling)
    addSolvers(simulation)
    robot = addRobot(simulation, modelling)
    robot.addObject("BoxROI", box=[0, 0, 0, 150, 10, 100])
    robot.addObject("FixedProjectiveConstraint", indices=robot.BoxROI.indices.linkpath, drawSize=1)

    def pressureAnimation(target, factor, pressure, startTime):
        from math import sin, pi
        if factor > 0:
            target.value.value = [sin(2 * pi * factor) * pressure]

    animate(pressureAnimation, {'target': robot.BodyCavity.SurfacePressureConstraint, 'pressure':0.5, 'startTime':0}, duration=2, mode="loop")
    animate(pressureAnimation, {'target': robot.HeadCavity1.SurfacePressureConstraint, 'pressure':1, 'startTime':0}, duration=2, mode="loop", terminationDelay=6)
    animate(pressureAnimation, {'target': robot.HeadCavity2.SurfacePressureConstraint, 'pressure':1, 'startTime':2}, duration=2, mode="loop", terminationDelay=6)
    animate(pressureAnimation, {'target': robot.HeadCavity3.SurfacePressureConstraint, 'pressure':1, 'startTime':4}, duration=2, mode="loop", terminationDelay=6)

