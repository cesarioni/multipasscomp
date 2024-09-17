import bpy
import os
import pathlib
import pprint
C = bpy.context
###INSTRUCTIONS:
#1.Create a volume material with the name of volume
#2.Put all the lights and cameras in one separate collection
#(if you click the delete collection button this collection will also be removed)
#The script will create a default view layer to render all the scene

#####################FUNCTIONS
####################Create collections functions

def setupRender():
    scene = bpy.context.scene
    scene.use_nodes = True
    offset = 5500
    remove_compositor_nodes()
    #thePasses = setupRenderPasses()
    FileBaseName = getFileBaseName()
    #loop on every view layer
    for counter, viewLayer in enumerate(bpy.context.scene.view_layers):
        thePasses = setupRenderPasses(viewLayer)
        #create main render layer and multiEXR
        setupMultiEXR(FileBaseName, viewLayer.name, 0, offset*counter) 
        #Create routes for passes
        PassesArray = setupCombinePasses(thePasses, 3400, (offset*counter)-50, viewLayer.name)
        #Create routes for lightgroups
        setupLGs(PassesArray[1], 3400, (offset*counter)-50, viewLayer.name, True)  
        #setupLGs(3400, (offset*counter)-50, viewLayer.name, False)
        #node to import the multiEXR
        createImageNode(2000, (offset*counter)-150)
        
def setupMultiEXR(path, name, xPos, yPos):
    render_layers_node = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeRLayers")
    render_layers_node.layer = name
    render_layers_node.location.y = yPos
    #Create exr output
    file_output_node = createOutputs(path + "_" + name, name, 1000, yPos-150)
    # Reset File Output node layer slots and match them to enabled Render Layers
    file_output_node.layer_slots.clear()
    # Only keep the enabled outputs
    for count, socket in enumerate(render_layers_node.outputs):
            if socket.enabled:
                file_output_node.layer_slots.new(socket.name)
    # Connect the sockets between the two nodes
    for i, socket in enumerate([s for s in render_layers_node.outputs if s.enabled]):
            bpy.context.scene.node_tree.links.new(file_output_node.inputs[i], socket)
    
def createImageNode(xPos, yPos):
    imageNode = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeImage")
    positionNodes(imageNode, xPos, yPos)
    return imageNode

def setupCombinePasses(thePasses, xPos, yPos, viewLayerName):
    reroutesArray=[]
    ofsset=150
    for count, thePass in enumerate(thePasses):
        currentReroute = createDot(thePass ,xPos, yPos-ofsset*count)
        currentSwitch = createSwitch(xPos-500, yPos-ofsset*count, thePass)
        reroutesArray.append(currentReroute)
        bpy.context.scene.node_tree.links.new(currentSwitch.outputs[0], currentReroute.inputs[0])
    passesOperation(reroutesArray, viewLayerName)
    return reroutesArray

def passesOperation(PassReroute, viewLayerName):
    lightCombined = combineElements(PassReroute[4], PassReroute[5], 'ADD', 1)
    diffLight = combineElements(lightCombined, PassReroute[6], 'MULTIPLY', 2)
    glossyCombined = combineElements(PassReroute[7], PassReroute[8], 'ADD', 1)
    diffGlossy = combineElements(glossyCombined , PassReroute[9], 'MULTIPLY', 2)
    transCombined = combineElements(PassReroute[10], PassReroute[11], 'ADD', 1)
    diffTrans = combineElements(transCombined , PassReroute[12], 'MULTIPLY', 2)
    transLightCombined = combineElements(diffLight, diffTrans, 'ADD', 3)
    totalGlossyCombined = combineElements(diffGlossy, transLightCombined, 'ADD', 3.5)
    addMist = combineElements(totalGlossyCombined, PassReroute[3], 'ADD', 3)
    copyAlpha_passes = getAlpha(addMist, PassReroute[1])

    #Copy the alpha to all passes
    diffAlpha = getAlpha(PassReroute[6], PassReroute[1], 30)
    lightAlpha = getAlpha(lightCombined, PassReroute[1], 30)
    glossyAlpha = getAlpha(diffGlossy, PassReroute[1], 30)
    transmitionAlpha = getAlpha(diffTrans, PassReroute[1], 30)
    mistAlpha = getAlpha(PassReroute[3], PassReroute[1], 30)
    
    #creating the output node and connecting to the passes with alpha
    
    file_output_Comp_Passes = createOutputsB(copyAlpha_passes,viewLayerName, 'OPEN_EXR', 'comp')
    file_output_Diffuse = createOutputsB(diffAlpha,viewLayerName, 'OPEN_EXR', 'Diffuse')
    file_output_Light = createOutputsB(lightAlpha ,viewLayerName, 'OPEN_EXR', 'Lighting')
    file_output_Glossy = createOutputsB(glossyAlpha,viewLayerName, 'OPEN_EXR', 'Specular')
    file_output_Transmition = createOutputsB(transmitionAlpha,viewLayerName, 'OPEN_EXR', 'Transmition')
    file_output_Mist = createOutputsB(mistAlpha,viewLayerName, 'OPEN_EXR', 'Mist')
    file_output_Image = createOutputsB(PassReroute[0],viewLayerName, 'OPEN_EXR', 'Image')


def setupLGs(theAlpha, xPos, yPos, viewLayerName, passesActive):
    knotsArray= []
    addArray = []
    ofsset=150
    separation = 15
    LGs= bpy.context.scene.view_layers[viewLayerName].lightgroups
    numLG = len(LGs)
    if len(LGs) > 0:##checks if lightgroups exists in curretnview layer
        if (passesActive == False):
            ##createdots and addMixNodes for alpha
            ofsset=0
            SwitchNodeAlpha = createSwitch(xPos-500, yPos-ofsset*(separation), "alpha")
            theAlpha1 = rerouteLGAlpha = createDot("alpha",xPos, yPos-ofsset*(separation))
            bpy.context.scene.node_tree.links.new(SwitchNodeAlpha.outputs[0], rerouteLGAlpha.inputs[0])
        ##createdots and addMixNodes
        for i, LG in enumerate(LGs):
            SwitchNode = createSwitch(xPos-500, yPos-ofsset*(separation+i+1), LGs[i].name)
            rerouteLG = createDot(LGs[i].name,xPos, yPos-ofsset*(separation+i+1))
            bpy.context.scene.node_tree.links.new(SwitchNode.outputs[0], rerouteLG.inputs[0])
            knotsArray.append(rerouteLG)
            if i < numLG-1:
                AddNode = createMixNode('ADD', rerouteLG.location.x+50+(200*i), rerouteLG.location.y)
                addArray.append(AddNode)     
        ##Connect nodes    
        for i in range(numLG):
            if i==0:
                ##Connect first dots to add nodes  
                connectAdds(knotsArray[i],addArray[i],0,1)
            else:
                ##Connect dots to add nodes 
                connectAdds(knotsArray[i],addArray[i-1],0,2)
            if i < numLG-2:
                ##Connect add nodes in sequence
                connectAdds(addArray[i],addArray[i+1],0,1)
                
        copyAlpha_LG = getAlpha(addArray[numLG-2], theAlpha)
        file_output_Comp_LG = createOutputsB(copyAlpha_LG,viewLayerName, 'OPEN_EXR', 'compLG')    
    return knotsArray
    
def connectAdds(element1, element2, output1, input1):
    bpy.context.scene.node_tree.links.new(element1.outputs[output1], element2.inputs[input1])

def createDot(mylabel,xPos,yPos):
    rerouteNode = bpy.context.scene.node_tree.nodes.new(type="NodeReroute")
    rerouteNode.label = mylabel
    rerouteNode.location=[xPos, yPos]
    return rerouteNode

def createSwitch(xPos, yPos, label):
    nodeSwitch = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeSwitch")
    nodeSwitch.location=[xPos, yPos]
    nodeSwitch.label= label
    return nodeSwitch
    
def combineElements(element1, element2, mathOp, posOffset):
    theoffset = 100 * posOffset
    mixNode = createMixNode(mathOp, element1.location.x+theoffset , element1.location.y)
    bpy.context.scene.node_tree.links.new(element1.outputs[0], mixNode .inputs[1])
    bpy.context.scene.node_tree.links.new(element2.outputs[0], mixNode .inputs[2])
    mixNode.hide=True
    return mixNode

def getAlpha(element, alphaOutput, posOffset = 500):
    setAlphaNode = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeSetAlpha")
    #setAlphaNode.mode = 'REPLACE_ALPHA'
    positionNodes(setAlphaNode, element.location.x+posOffset, element.location.y)
    bpy.context.scene.node_tree.links.new(element.outputs[0], setAlphaNode.inputs[0])
    bpy.context.scene.node_tree.links.new(alphaOutput.outputs[0], setAlphaNode.inputs[1])
    setAlphaNode.hide=True
    return setAlphaNode

def createMixNode(blendType, xPos, yPos):
    mixNode = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeMixRGB")
    mixNode.blend_type= blendType
    positionNodes(mixNode, xPos, yPos)
    mixNode.hide=True
    return mixNode

def createOutputs(nameFile, prefix, xPos, yPos):
    render_output = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeOutputFile")
    filepath = bpy.data.filepath
    subPath = os.path.join(os.path.dirname(filepath), getFileBaseName()+"_"+prefix)
    render_output.base_path=subPath
    render_output.format.file_format='OPEN_EXR_MULTILAYER'
    render_output.format.color_depth='32'
    render_output.format.color_management = 'OVERRIDE'
    render_output.format.view_settings.view_transform='Standard'
    positionNodes(render_output, xPos, yPos)
    return render_output

def createOutputsB(element, prefix, format, filename):
    render_output = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeOutputFile")
    render_output.layer_slots.clear()
    render_output.layer_slots.new(filename)
    filepath = bpy.data.filepath
    subPath = os.path.join(os.path.dirname(filepath), "Layer_"+prefix)
    render_output.base_path=subPath
    render_output.format.file_format='OPEN_EXR'
    render_output.format.color_depth='32'
    render_output.format.color_management = 'OVERRIDE'
    render_output.format.view_settings.view_transform='Standard'
    positionNodes(render_output, element.location.x+20, element.location.y+20)
    bpy.context.scene.node_tree.links.new(element.outputs[0], render_output.inputs[0])
    render_output.hide = True
    return render_output

def getFileBaseName():
    fileName = bpy.path.basename(bpy.context.blend_data.filepath)
    fileName = fileName.split(".")
    baseName = fileName[0]
    baseName = baseName.split("_")
    return baseName[0]

def positionNodes(myNode, xPos, yPos):
    myNode.location.x = xPos
    myNode.location.y = yPos
    
def remove_compositor_nodes():
    bpy.context.scene.use_nodes = True
    bpy.context.scene.node_tree.nodes.clear()
  
def setupRenderPasses(theViewLayer, usePasses = True):
    passes = []
    passes.append("NoisyImage")
    passes.append("Alpha")
    theViewLayer.use_pass_z = True
    passes.append("ZDepth")
    theViewLayer.use_pass_mist = True
    passes.append("Mist")
    theViewLayer.use_pass_diffuse_direct = True
    passes.append("DiffDir")
    theViewLayer.use_pass_diffuse_indirect = True
    passes.append("DiffInd")
    theViewLayer.use_pass_diffuse_color = True
    passes.append("DiffCol")
    theViewLayer.use_pass_glossy_direct = True
    passes.append("GlossDir")
    theViewLayer.use_pass_glossy_indirect = True
    passes.append("GlossInd")
    theViewLayer.use_pass_glossy_color = True
    passes.append("GlossCol")
    theViewLayer.use_pass_transmission_direct = True
    passes.append("TransDir")
    theViewLayer.use_pass_transmission_indirect = True
    passes.append("TransInd")
    theViewLayer.use_pass_transmission_color = True
    passes.append("TransCol")
    return passes  
     
setupRender()
