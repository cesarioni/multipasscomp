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
    remove_compositor_nodes()
    scene = bpy.context.scene
    scene.use_nodes = True
    counter=0
    offset = 5500
    FileBaseName = getFileBaseName()
    
    for viewLayer in bpy.context.scene.view_layers:
        #compositor_node_tree = scene.node_tree
        render_layers_node = scene.node_tree.nodes.new(type="CompositorNodeRLayers")
        render_layers_node.layer= viewLayer.name
        render_layers_node.location.y=offset*counter

        #Create exr outputs
        file_output_node = createOutputs(FileBaseName + "_" + viewLayer.name, viewLayer.name, 1000, (offset*counter)-150)
        # Reset File Output node layer slots and match them to enabled Render Layers
        file_output_node.layer_slots.clear()
        
        # Only keep the enabled outputs
        for count, socket in enumerate(render_layers_node.outputs):
            if socket.enabled:
                file_output_node.layer_slots.new(socket.name)
                #createPassReroute(3400, (offset*counter)-50, viewLayer.name, socket.name, count)
        
        # Connect the sockets between the two nodes
        for i, socket in enumerate([s for s in render_layers_node.outputs if s.enabled]):
            bpy.context.scene.node_tree.links.new(file_output_node.inputs[i], socket)
            
        createImageNode(2000, (offset*counter)-150)
        createReroutes(3400, (offset*counter)-50, viewLayer.name)
        counter+=1
        
def setupRenderPasses():
    for theViewLayer in bpy.context.scene.view_layers:
        theViewLayer.use_pass_mist = True
        theViewLayer.use_pass_diffuse_direct = True
        theViewLayer.use_pass_diffuse_indirect = True
        theViewLayer.use_pass_diffuse_color = True
        theViewLayer.use_pass_glossy_direct = True
        theViewLayer.use_pass_glossy_indirect = True
        theViewLayer.use_pass_glossy_color = True
        theViewLayer.use_pass_transmission_direct = True
        theViewLayer.use_pass_transmission_indirect = True
        theViewLayer.use_pass_transmission_color = True
    
def createImageNode(xPos, yPos):
    #print (bpy.context.scene.view_layers["Environment"].RenderPasses)
    imageNode = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeImage")
    positionNodes(imageNode, xPos, yPos)
    return imageNode

def createPassReroute(xPos, yPos, viewLayerName, label, loopVar = 1):
    ofsset=150
    rerouteMist = createDot(label,xPos, yPos-ofsset*loopVar)

def createReroutes(xPos, yPos, viewLayerName):
    ofsset=150
    print(bpy.context.scene.view_layers[viewLayerName].aovs)
    
    rerouteMist = createDot("Mist",xPos, yPos-ofsset*1)
    rerouteDiffDir = createDot("DiffDir",xPos, yPos-ofsset*2)
    rerouteDiffInd = createDot("DiffInd",xPos, yPos-ofsset*3)
    rerouteDiffCol = createDot("DiffCol",xPos, yPos-ofsset*4)
    rerouteGlossDir = createDot("GlossDir",xPos, yPos-ofsset*5)
    rerouteGlossInd = createDot("GlossInd",xPos, yPos-ofsset*6)
    rerouteGlossCol = createDot("GlossCol",xPos, yPos-ofsset*7)
    rerouteTransDir = createDot("TransDir",xPos, yPos-ofsset*8)
    rerouteTransInd = createDot("TransInd",xPos, yPos-ofsset*9)
    rerouteTransCol = createDot("TransCol",xPos, yPos-ofsset*10)
    rerouteAlpha = createDot("Alpha",xPos, yPos-ofsset*11)
    rerouteImage = createDot("NoisyImage",xPos, yPos-ofsset*12)
    rerouteZ = createDot("ZDepth",xPos, yPos-ofsset*13)
    

    switchArray=[]
    for i in range (13):
        currentSwitch = createSwitch(xPos-500, yPos-ofsset*i)
        switchArray.append(currentSwitch)
        
    bpy.context.scene.node_tree.links.new(switchArray[0].outputs[0], rerouteMist.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[1].outputs[0], rerouteDiffDir.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[2].outputs[0], rerouteDiffInd.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[3].outputs[0], rerouteDiffCol.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[4].outputs[0], rerouteGlossDir.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[5].outputs[0], rerouteGlossInd.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[6].outputs[0], rerouteGlossCol.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[7].outputs[0], rerouteTransDir.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[8].outputs[0], rerouteTransInd.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[9].outputs[0], rerouteTransCol.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[10].outputs[0], rerouteAlpha.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[11].outputs[0], rerouteImage.inputs[0])
    bpy.context.scene.node_tree.links.new(switchArray[12].outputs[0], rerouteZ.inputs[0])
    
    lightCombined = combineElements(rerouteDiffDir, rerouteDiffInd, 'ADD', 1)
    diffLight = combineElements(lightCombined, rerouteDiffCol, 'MULTIPLY', 2)
    
    glossyCombined = combineElements(rerouteGlossDir, rerouteGlossInd, 'ADD', 1)
    diffGlossy = combineElements(glossyCombined , rerouteGlossCol, 'MULTIPLY', 2)
    
    transCombined = combineElements(rerouteTransDir, rerouteTransInd, 'ADD', 1)
    diffTrans = combineElements(transCombined , rerouteTransCol, 'MULTIPLY', 2)
    
    transLightCombined = combineElements(diffLight, diffTrans, 'ADD', 3)
    
    totalGlossyCombined = combineElements(diffGlossy, transLightCombined, 'ADD', 3.5)
    
    addMist = combineElements(totalGlossyCombined, rerouteMist, 'ADD', 3)
      
    copyAlpha_passes = getAlpha(addMist, rerouteAlpha)
    
    ####light group setup
    numLG = len(bpy.context.scene.view_layers[viewLayerName].lightgroups)
    knotsArray= []
    addArray = []
    if numLG > 0:##checks if lightgroups exists in curretnview layer
        ##createdots and addMixNodes
        for i in range(numLG):
            SwitchNode = createSwitch(xPos-500, yPos-ofsset*(15+i))
            rerouteLG = createDot("LG"+str(i),xPos, yPos-ofsset*(15+i))
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
                
        copyAlpha_LG = getAlpha(addArray[numLG-2], rerouteAlpha)
        file_output_Comp_LG = createOutputsB(copyAlpha_LG,viewLayerName, 'OPEN_EXR', 'compLG')         
        


    ###OUTPUTS
    #Copy the alpha to all passes
    diffAlpha = getAlpha(rerouteDiffCol, rerouteAlpha, 30)
    lightAlpha = getAlpha(lightCombined, rerouteAlpha, 30)
    glossyAlpha = getAlpha(diffGlossy, rerouteAlpha, 30)
    transmitionAlpha = getAlpha(diffTrans, rerouteAlpha, 30)
    mistAlpha = getAlpha(rerouteMist, rerouteAlpha, 30)
    
    #creating the output node and connecting to the passes with alpha
    
    ############file_output_Comp_LG = createOutputsB(copyAlpha_LG,viewLayerName, 'OPEN_EXR', 'comp')
    file_output_Comp_Passes = createOutputsB(copyAlpha_passes,viewLayerName, 'OPEN_EXR', 'comp')
    
    file_output_Diffuse = createOutputsB(diffAlpha,viewLayerName, 'OPEN_EXR', 'Diffuse')
    file_output_Light = createOutputsB(lightAlpha ,viewLayerName, 'OPEN_EXR', 'Lighting')
    file_output_Glossy = createOutputsB(glossyAlpha,viewLayerName, 'OPEN_EXR', 'Specular')
    file_output_Transmition = createOutputsB(transmitionAlpha,viewLayerName, 'OPEN_EXR', 'Transmition')
    file_output_Mist = createOutputsB(mistAlpha,viewLayerName, 'OPEN_EXR', 'Mist')
    file_output_Image = createOutputsB(rerouteImage,viewLayerName, 'OPEN_EXR', 'Image')
    
def connectAdds(element1, element2, output1, input1):
    bpy.context.scene.node_tree.links.new(element1.outputs[output1], element2.inputs[input1])

def createDot(mylabel,xPos,yPos):
    rerouteNode = bpy.context.scene.node_tree.nodes.new(type="NodeReroute")
    rerouteNode.label = mylabel
    rerouteNode.location=[xPos, yPos]
    return rerouteNode

def createSwitch(xPos, yPos):
    nodeSwitch = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeSwitch")
    nodeSwitch.location=[xPos, yPos]
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
    bpy.context.scene.node_tree.nodes.clear()
 
setupRenderPasses()        
setupRender()
