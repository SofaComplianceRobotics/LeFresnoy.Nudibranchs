from math import pi, sin, cos
import parameters as params
import Sofa.ImGui as MyGui


# Units are mm, kg, s
def addRobot(simulation, modelling, meshGeneration=True):

    robot = simulation.addChild("Robot")
    robot.addObject("MeshTopology", src=modelling.BodyVolume.topology.linkpath)

    robot.addObject("MechanicalObject")
    # Young's modulus is 
    #  - 69 kPa for silicone ecoflex 30
    #  - 55 kPa for silicone ecoflex 10
    #  - 590 kPa for silicone dragon skin 30
    #  - 150 kPa for silicone dragon skin 10
    # kPa -> kg/(mm.s^2)
    robot.addObject("ParallelTetrahedronFEMForceField", youngModulus=590, poissonRatio=0.49)


    volume = robot.addChild("Volume")
    volume.addObject("VolumeFromTetrahedrons", src=modelling.BodyVolume.MeshTopology.linkpath)
    # density is 1e-6 kg/mm^3 for all silicones  
    # volume is 2.7e6 mm^3
    # mass is 2.7 kg

    robot.addObject("UniformMass", totalMass=2.7)

    if not params.COARSE:
        visual = robot.addChild("Visual")
        visual.addObject("MeshTopology", src=modelling.BodySurface.MeshTopology.linkpath)
        visual.addObject("OglModel", src=visual.MeshTopology.linkpath, color=[1., 1., 1., 1.])
        visual.addObject("BarycentricMapping")

    # Sphere:
    # rest volume: 505201.749 mm3
    # volume growth: 167003.831 mm3
    # Accordion:
    # rest volume: 87144.807 mm3
    # volume growth: 23532.724 mm3
    cavity = robot.addChild("BodyCavity")
    cavity.addObject("MeshTopology", src=modelling.BodyCavity.MeshTopology.linkpath)
    cavity.addObject("MechanicalObject")
    cavity.addObject("SurfacePressureConstraint", value=0, valueType="pressure")
    cavity.addObject("BarycentricMapping")

    def addRings(node, radius=7, nbRings=10, length=60, nbSections=10):
        rings = node.addChild('rings')
        for k in range(nbRings):
            positions = []
            for j in range(nbSections + 1):
                theta = 2 * pi / nbSections * j
                positions += [radius * sin(theta), radius * cos(theta),
                              length / nbRings * k + length / (nbRings * 2)]

            ring = rings.addChild('ring' + str(k))
            ring.addObject("VisualStyle", displayFlags="showBehavior")
            ring.addObject('EdgeSetTopologyContainer',
                           position=positions,
                           edges=[[l, l + 1] for l in range(nbSections)])
            ring.addObject('MechanicalObject',
                           rotation=params.rotation,
                           translation=params.translation[i],
                           scale3d=params.scale)
            ring.addObject('UniformMass', totalMass=1e-6)
            ring.addObject('MeshSpringForceField', stiffness=1.5e5, damping=0)
            ring.addObject('BarycentricMapping')

    for i in range(3):
        # rest volume: 14071.429 mm3
        # volume growth: 4129.607 mm3
        cavity = robot.addChild("HeadCavity" + str(i + 1))
        cavity.addObject("MeshTopology", src=modelling.getChild("HeadCavity" + str(i + 1)).MeshTopology.linkpath)
        cavity.addObject("MechanicalObject",
                         rotation=params.rotation if not meshGeneration else [0, 0, 0],
                         translation=params.translation[i] if not meshGeneration else [0, 0, 0],
                         scale3d=params.scale if not meshGeneration else [1, 1, 1])
        # 0.3 bar -> 30 kPa -> 30 kg/(mm.s^2)
        cavity.addObject("SurfacePressureConstraint", value=0, valueType="pressure")
        cavity.addObject("BarycentricMapping")

        if not meshGeneration:
            addRings(cavity)



    return robot

def createScene(rootnode):
    from header import addHeader, addSolvers
    from scene import addRobot

    settings, modelling, simulation = addHeader(rootnode)

    settings.addObject("RequiredPlugin", name="CGALPlugin")
    settings.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')  # Needed to use components [MeshSTLLoader]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Constant')  # Needed to use components [MeshTopology]
    settings.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')  # Needed to use components [OglModel]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Projective')  # Needed to use components [FixedProjectiveConstraint]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Engine.Select')  # Needed to use components [BoxROI]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Mapping.Linear')  # Needed to use components [BarycentricMapping]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Mass')  # Needed to use components [UniformMass]
    settings.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.Spring')  # Needed to use components [MeshSpringForceField]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Dynamic')  # Needed to use components [EdgeSetTopologyContainer]

    rootnode.VisualStyle.displayFlags=["showVisual", "showBehavior", "showWireFrame"]
    rootnode.gravity.value = [0, 0, -9810]
    #rootnode.addObject("ClipPlane", position=[0, 0, 0], normal=[0, 1, 0])

    bodysurface = modelling.addChild("BodySurface")
    bodysurface.addObject("MeshSTLLoader", filename="mesh/body.stl")
    bodysurface.addObject("MeshTopology", src=bodysurface.MeshSTLLoader.linkpath)

    bodycavity = modelling.addChild("BodyCavity")
    bodycavityMesh = "mesh/bodycavity_sphere.stl" if params.cavity == "sphere" else "mesh/bodycavity_accordion.stl"
    bodycavity.addObject("MeshSTLLoader", filename=bodycavityMesh)
    bodycavity.addObject("MeshTopology", src=bodycavity.MeshSTLLoader.linkpath)

    for i in range(3):
        headcavity = modelling.addChild("HeadCavity" + str(i + 1))
        headcavity.addObject("MeshSTLLoader", filename="mesh/headcavity.stl")
        headcavity.addObject("MeshTopology", src=headcavity.MeshSTLLoader.linkpath)

    bodyvolume = modelling.addChild("BodyVolume")

    typeName = "coarse" if params.COARSE else "fine"
    bodyvolume.addObject("MeshVTKLoader", filename="mesh/body_"+params.cavity+"_"+typeName+"0.vtu")
    bodyvolume.addObject("MeshTopology", src=bodyvolume.MeshVTKLoader.linkpath)

    addSolvers(simulation)
    robot = addRobot(simulation, modelling, meshGeneration=False)
    robot.addObject("BoxROI", box=[-100, 0, -100, 100, 400, -60])
    robot.addObject("FixedProjectiveConstraint", indices=robot.BoxROI.indices.linkpath, drawSize=0)

    group = "Pressure (kPa)"
    MyGui.MyRobotWindow.addSettingInGroup("Body", robot.BodyCavity.SurfacePressureConstraint.value, 0, 1, group)
    MyGui.MyRobotWindow.addSettingInGroup("Head down", robot.HeadCavity1.SurfacePressureConstraint.value, 0, 8, group)
    MyGui.MyRobotWindow.addSettingInGroup("Head left", robot.HeadCavity2.SurfacePressureConstraint.value, 0, 8, group)
    MyGui.MyRobotWindow.addSettingInGroup("Head right", robot.HeadCavity3.SurfacePressureConstraint.value, 0, 8, group)
