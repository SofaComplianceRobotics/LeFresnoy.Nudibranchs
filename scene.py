
def addRobot(simulation, modelling):

    robot = simulation.addChild("Robot")
    robot.addObject("MeshTopology", src=modelling.BodyVolume.MeshTopology.linkpath)

    robot.addObject("MechanicalObject")
    robot.addObject("TetrahedronFEMForceField", youngModulus=180, poissonRatio=0.49)
    robot.addObject("UniformMass", totalMass=1)

    cavity = robot.addChild("BodyCavity")
    cavity.addObject("MeshTopology", src=modelling.BodyCavity.MeshTopology.linkpath)
    cavity.addObject("MechanicalObject")
    cavity.addObject("SurfacePressureConstraint", value=0, valueType="pressure")
    cavity.addObject("BarycentricMapping")

    for i in range(3):
        # TODO: add springs to orientate expansion
        cavity = robot.addChild("HeadCavity" + str(i + 1))
        cavity.addObject("MeshTopology", src=modelling.getChild("HeadCavity" + str(i + 1)).MeshTopology.linkpath)
        cavity.addObject("MechanicalObject")
        cavity.addObject("SurfacePressureConstraint", value=0, valueType="pressure")
        cavity.addObject("BarycentricMapping")

    return robot

# TODO : write a scene that uses saved generated meshes