from math import pi, sin, cos
import parameters as params


# Units are mm, kg, s
def addRobot(simulation, modelling, meshGeneration=True):

    robot = simulation.addChild("Robot")
    robot.addObject("MeshTopology", src=modelling.BodyVolume.topology.linkpath)

    robot.addObject("MechanicalObject")
    robot.addObject("ParallelTetrahedronFEMForceField", youngModulus=280, poissonRatio=0.49)
    robot.addObject("UniformMass", totalMass=1.5)

    if not params.COARSE:
        visual = robot.addChild("Visual")
        visual.addObject("MeshTopology", src=modelling.BodySurface.MeshTopology.linkpath)
        visual.addObject("OglModel", src=visual.MeshTopology.linkpath, color=[0.5, 0.5, 0.5, 0.9])
        visual.addObject("BarycentricMapping")

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
        cavity = robot.addChild("HeadCavity" + str(i + 1))
        cavity.addObject("MeshTopology", src=modelling.getChild("HeadCavity" + str(i + 1)).MeshTopology.linkpath)
        cavity.addObject("MechanicalObject",
                         rotation=params.rotation if not meshGeneration else [0, 0, 0],
                         translation=params.translation[i] if not meshGeneration else [0, 0, 0],
                         scale3d=params.scale if not meshGeneration else [1, 1, 1])
        cavity.addObject("SurfacePressureConstraint", value=0, valueType="pressure")
        cavity.addObject("BarycentricMapping")

        if not meshGeneration:
            addRings(cavity)



    return robot

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
    settings.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Projective')  # Needed to use components [FixedProjectiveConstraint]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Engine.Select')  # Needed to use components [BoxROI]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Mapping.Linear')  # Needed to use components [BarycentricMapping]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Mass')  # Needed to use components [UniformMass]
    settings.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.Spring')  # Needed to use components [MeshSpringForceField]
    settings.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Dynamic')  # Needed to use components [EdgeSetTopologyContainer]

    rootnode.VisualStyle.displayFlags=["showVisual", "showBehavior"]
    rootnode.gravity.value = [0, 0, -9810]
    # rootnode.addObject("ClipPlane", position=[0, 0, 0], normal=[0, 1, 0])

    bodysurface = modelling.addChild("BodySurface")
    bodysurface.addObject("MeshSTLLoader", filename="mesh/body.stl")
    bodysurface.addObject("MeshTopology", src=bodysurface.MeshSTLLoader.linkpath)

    bodycavity = modelling.addChild("BodyCavity")
    bodycavity.addObject("MeshSTLLoader", filename="mesh/bodycavity.stl")
    bodycavity.addObject("MeshTopology", src=bodycavity.MeshSTLLoader.linkpath)

    for i in range(3):
        headcavity = modelling.addChild("HeadCavity" + str(i + 1))
        headcavity.addObject("MeshSTLLoader", filename="mesh/headcavity.stl")
        headcavity.addObject("MeshTopology", src=headcavity.MeshSTLLoader.linkpath)

    bodyvolume = modelling.addChild("BodyVolume")

    bodyvolume.addObject("MeshVTKLoader", filename="mesh/body0_coarse.vtu" if params.COARSE else "mesh/body0_fine.vtu")
    bodyvolume.addObject("MeshTopology", src=bodyvolume.MeshVTKLoader.linkpath)

    addSolvers(simulation)
    robot = addRobot(simulation, modelling, meshGeneration=False)
    robot.addObject("BoxROI", box=[-100, 0, -100, 100, 400, -60])
    robot.addObject("FixedProjectiveConstraint", indices=robot.BoxROI.indices.linkpath, drawSize=2)

    def pressureAnimation(target, factor, pressure, startTime):
        from math import sin, pi
        if factor > 0:
            target.value.value = [sin(2 * pi * factor) * pressure]

    animate(pressureAnimation, {'target': robot.BodyCavity.SurfacePressureConstraint, 'pressure':0.5, 'startTime':0}, duration=2, mode="loop")
    animate(pressureAnimation, {'target': robot.HeadCavity1.SurfacePressureConstraint, 'pressure':4., 'startTime':0}, duration=2, mode="loop", terminationDelay=6)
    animate(pressureAnimation, {'target': robot.HeadCavity2.SurfacePressureConstraint, 'pressure':4., 'startTime':2}, duration=2, mode="loop", terminationDelay=6)
    animate(pressureAnimation, {'target': robot.HeadCavity3.SurfacePressureConstraint, 'pressure':4., 'startTime':4}, duration=2, mode="loop", terminationDelay=6)
