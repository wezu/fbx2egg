import os, sys

def buildVertexData(fbx_data, vertId, rgba, uv, tbnId=None):
    if tbnId==None:
        tbnId=vertId
    xyz=(fbx_data['Vertices'][index][int(vertId)*3],
         fbx_data['Vertices'][index][int(vertId)*3+1],
         fbx_data['Vertices'][index][int(vertId)*3+2])
    try:     
        n=(fbx_data['Normals'][index][int(tbnId)*3],
           fbx_data['Normals'][index][int(tbnId)*3+1],
           fbx_data['Normals'][index][int(tbnId)*3+2])
    except:        
        n=None
    try:    
        t=(fbx_data['Tangents'][index][int(tbnId)*3],
           fbx_data['Tangents'][index][int(tbnId)*3+1],
           fbx_data['Tangents'][index][int(tbnId)*3+2])
    except:        
        t=None
    try:    
        b=(fbx_data['Binormals'][index][int(tbnId)*3],
           fbx_data['Binormals'][index][int(tbnId)*3+1],
           fbx_data['Binormals'][index][int(tbnId)*3+2])
    except:        
        b=None      
    if rgba:
        rgba=rgba[tbnId]
    else:        
        rgba=(1,1,1,1)        
    if uv: 
         uv=temp_uv[tbnId]  
    else:        
        uv=(0,0)
    vert_dict={'xyz':xyz, 'n':n, 't':t, 'b':b, 'rgba':rgba, 'uv':uv}
    return vert_dict
    
in_file=sys.argv[1]
out_file=sys.argv[2]

#what are we looking for in the fbx?
fbx_data={'Vertices':[],
        'PolygonVertexIndex':[],
        'Normals':[],
        'Tangents':[],
        'Binormals':[],
        'UV':[],
        'UVIndex':[],
        'Colors':[],
        'ColorIndex':[],
        'Model:':[], #can be Mesh or LimbNode
        'Node':[],#will point to a UI of the matrix that should come next
        'Matrix':[],
        'Deformer':[],# can be "Skin"(useless) or "Cluster" (needed!)
        'Indexes':[],# these should be indexes for weights
        'Weights':[],#membership
        'Transform':[], #not sure yet, looks important
        'TransformLink':[], #not sure yet, looks important
        'Texture:':[],
        'RelativeFilename':[], #texture path, duplicated :|         
        'C: ':[], #Connections
        'AnimationCurve':[], #animations (probably only tht UId is of use)
        'KeyValueFloat':[], #animations
        'Material:':[],
        'P: "DiffuseColor"':[], #material diffuse
        'P: "AmbientColor"':[], #material ambient
        'P: "SpecularColor"':[], #material specular
        'P: "Shininess"':[], #material shininess != <Scalar> shininess { number } ???
        'P: "EmissiveColor"':[] #material emissive
        }
#how to format the data?
fbx_format={'Vertices':        lambda x: x.strip('a: ').split(','),
        'PolygonVertexIndex':  lambda x: x.strip('a: ').split(','),
        'Normals':             lambda x: x.strip('a: ').split(','),
        'Tangents':            lambda x: x.strip('a: ').split(','),
        'Binormals':           lambda x: x.strip('a: ').split(','),
        'UV':                  lambda x: x.strip('a: ').split(','),
        'UVIndex':             lambda x: x.strip('a: ').split(','),
        'Colors':              lambda x: x.strip('a: ').split(','),
        'ColorIndex':          lambda x: x.strip('a: ').split(','),
        'Model:':              lambda x: (last_line.split(',')[0].strip('Model: '), last_line.split(',')[1].strip('"Model:: "'),last_line.split(',')[2].strip(' {')),
        'Node':                lambda x: last_line.split(' ')[1],
        'Matrix':              lambda x: x.strip('a: ').split(','),
        'Deformer':            lambda x: None,
        'Indexes':             lambda x: None,
        'Weights':             lambda x: None,
        'Transform':           lambda x: None,
        'TransformLink':       lambda x: None,
        'Texture:':            lambda x: (last_line.split(',')[0].strip('Texture: '), last_line.split(',')[1].strip('"Texture:: "')),
        'RelativeFilename':    lambda x: (last_line.split(': ')[1].strip('"')),# if last_line_type=='Texture:' else None),
        'C: ':                 lambda x: (last_line.split(',')),
        'AnimationCurve':      lambda x: None,
        'KeyValueFloat':       lambda x: None,
        'Material:':           lambda x: None,
        'P: "DiffuseColor"':   lambda x: None,
        'P: "AmbientColor"':   lambda x: None,
        'P: "SpecularColor"':  lambda x: None,
        'P: "Shininess"':      lambda x: None,
        'P: "EmissiveColor"':  lambda x: None
        }        

line_type=None
last_line=""
last_line_type=None
#read the fbx file
with open(in_file,'r') as fbx:
    for line in fbx:
        line=line.strip().strip('\n')
        if line_type in fbx_data:
            data=fbx_format[line_type](line)
            if data:
                fbx_data[line_type].append(data)            
            line_type=None
            last_line_type=line_type
        for key in fbx_data:
            if line.startswith(key):
                line_type=key
        last_line=line      
         
#data needed to build an egg file
egg_data={'Group':[],#{'name':'', id:''}
          'Vertex':{},#{'xyz':[], 'n':[], 'b':[], 't':[], 'uv':[], 'rgba':[]}
          'Polygon':{},#{'TRef':[],'VertexRef':[], 'id':''}???
          'Joint':[],#{'name:'', 'id':'', 'Transform':[], 'VertexRef':[(vertId,weight)]}???
          'Texture':{}
          }
#find groups and joints
for group in fbx_data['Model:']:
    if group[2]=='"Mesh"':
        egg_data['Group'].append({'name':group[1], 'id':group[0]})
        egg_data['Vertex'][group[0]]=[]
        egg_data['Polygon'][group[0]]=[]
        egg_data['Texture'][group[0]]=[]
    elif group[2]=='"LimbNode"':
        egg_data['Joint'].append({'name':group[1], 'id':group[0]})
    else:
        print "Unsupported Model type {0}".format(group[2])
 
#find textures
#in the fbx a texture is linked to a material, and the material is linked to a mesh
#in egg a texture is linked per polygon, but since there is o such info in the fbx
#we will link the texture to a group and apply it to each polygon in that group 
#in the fbx a texture can be described as DiffuseColor, Bump, NormalMap, EmissiveColor etc
#I'll try to turn that into a valid egg 'envtype' and use '<Scalar> envtype { modulate }' where I can't find a match 
known_tex_type={' "DiffuseColor"':              'modulate',
                ' "TransparentColor"':          'modulate', #??
                ' "Bump"':                      'normal',#or height? or normal_height?
                ' "NormalMap"':                 'normal',
                ' "EmissiveColor"':             'glow',
                ' "DisplacementColor"':         'height',#??
                ' "SpecularColor"':             'gloss',
                ' "ReflectionColor"':           'gloss',#??
                ' "AmbientColor"':              'modulate',#??
                ' "VectorDisplacementColor"':   'height'#??
                }
for tex in fbx_data['Texture:']:
    id=tex[0]
    material=None
    group_id=None
    file=fbx_data['RelativeFilename'][fbx_data['Texture:'].index(tex)]
    type=None
    #find the material
    for connection in fbx_data['C: ']:
        if connection[1]==id:
            material=connection[2]
            type=connection[3]
    #find the mesh/group        
    for connection in fbx_data['C: ']:
        if connection[1]==material:
            group_id=connection[2]   
    #translate the type
    if type in known_tex_type:
        type=known_tex_type[type]
    else:
        type='modulate'
    egg_data['Texture'][group_id].append({'file':file, 'type':type})
   
#build the data
for index, group in enumerate(egg_data['Group']):  
    temp_poly=[]
    poly=[]
    temp_uv=[]
    temp_color=[]
    temp_normal=[]
    temp_vert=[]
    temp_binormal=[]
    temp_tangent=[]
    for vert in fbx_data['PolygonVertexIndex'][index]:        
        #if the index is negative it's the 'last' vertex in a poly
        if int(vert)>-1:
            poly.append(vert)
        else:
            poly.append(int(vert)*(-1)-1)
            temp_poly.append(poly)
            poly=[]         
    #UV and colors should always be "IndexToDirect", 
    #UV are 2 element, colors are 4 element, verts are 3 element so they can't be "Direct"  
    try:
        for i in fbx_data['UVIndex'][index]:       
            temp_uv.append( (fbx_data['UV'][index][int(i)*2],
                             fbx_data['UV'][index][int(i)*2+1])
                             )
    except:
        pass
    #RGBA    
    try:    
        for i in fbx_data['ColorIndex'][index]:       
            temp_color.append( (fbx_data['Colors'][index][int(i)*4],
                                fbx_data['Colors'][index][int(i)*4+1],
                                fbx_data['Colors'][index][int(i)*4+2],
                                fbx_data['Colors'][index][int(i)*4+3])
                             )
    except:
        pass                         
    #normals (and tbn) can be "Direct" or "IndexToDirect"
    #in "IndexToDirect" mode there will be 1 normal per vert
    #in "Direct" some verts are implicit and we need to rebuild the vert and poly table                      
    if len(fbx_data['Normals'][index])==len(fbx_data['Vertices'][index]):        
        for vertId, data in enumerate(fbx_data['Vertices'][index]):           
            if vertId*3+2<len(fbx_data['Vertices'][index]): 
                vert_dict=buildVertexData(fbx_data, vertId, temp_color, temp_uv)                        
                egg_data['Vertex'][group['id']].append(vert_dict) 
        for polygon in temp_poly:  
            new_poly=[]
            for vertId in polygon:
                new_poly.append(vertId)
            egg_data['Polygon'][group['id']].append(new_poly)                                     
    else: 
        id=0
        for polygon in temp_poly:
            new_poly=[]
            for vertId in polygon:
                vert_dict=buildVertexData(fbx_data, vertId, temp_color, temp_uv, id)
                egg_data['Vertex'][group['id']].append(vert_dict)
                new_poly.append(id) 
                id+=1
            egg_data['Polygon'][group['id']].append(new_poly) 
                        
#write the egg file   
with open(out_file,'w') as egg:
    #TODO: get "UpAxis" from FBX
    egg.write('<CoordinateSystem> { Z-Up }\n\n')
    #Textures
    for tex in egg_data['Texture']:
        for index, temp in enumerate(egg_data['Texture'][tex]):        
            egg.write('<Texture> Tex{0} {{\n'.format(index))
            egg.write('{file}\n'.format(**egg_data['Texture'][tex][index]))
            #TODO: this should be set in the GUI.. once a GUI exist
            egg.write('<Scalar> format { rgb }\n')
            egg.write('<Scalar> wrapu { repeat }\n')
            egg.write('<Scalar> wrapv { repeat }\n')
            egg.write('<Scalar> minfilter { linear_mipmap_linear }\n')
            egg.write('<Scalar> magfilter { linear }\n')
            egg.write('<Scalar> envtype {{ {type} }}\n'.format(**egg_data['Texture'][tex][index]))
            #TODO: stage-name, compression, anisotropic-degree, alpha
            egg.write('}\n')
    for index, group in enumerate(egg_data['Group']):            
        egg.write('<Group> {name} {{\n'.format(**group))
        egg.write('    <VertexPool> {name}.verts {{\n'.format(**group))
        for id, vertex in enumerate(egg_data['Vertex'][group['id']]):
            v_data=egg_data['Vertex'][group['id']][id]
            egg.write('        <Vertex> {0} {{\n'.format(id))
            egg.write('        {xyz[0]} {xyz[1]} {xyz[2]}\n'.format(**v_data))
            egg.write('            <Normal> {{ {n[0]} {n[1]} {n[2]} }}\n'.format(**v_data))
            if v_data['rgba']:    
                egg.write('            <RGBA> {{ {rgba[0]} {rgba[1]} {rgba[2]} {rgba[3]} }}\n'.format(**v_data))
            egg.write('            <UV> {\n')
            egg.write('                {uv[0]} {uv[1]}\n'.format(**v_data))   
            if v_data['t']:   
                egg.write('                <Tangent> {{ {t[0]} {t[1]} {t[2]} }}\n'.format(**v_data))
            if v_data['b']:    
                egg.write('                <Binormal> {{ {b[0]} {b[1]} {b[2]} }}\n'.format(**v_data))
            egg.write('            }\n')
            egg.write('        }\n')
        egg.write('    }\n')     
        for poly in egg_data['Polygon'][group['id']]:
            egg.write('    <Polygon> {\n')
            egg.write('    <VertexRef> {  ')
            for v in poly:
                egg.write(str(v)+" ")
            egg.write(' <Ref> {{ {name}.verts }} }}\n'.format(**group))
            #textures
            for tex in egg_data['Texture']:
                if tex==group['id']:
                    for i, temp in enumerate(egg_data['Texture'][tex]):
                        egg.write('    <TRef> {{ Tex{0} }}\n'.format(i))
            egg.write('    }\n')
        egg.write('}')
  