import os, sys

def add(s1, s2):
    return float(s1)+float(s2)
def mul(s1, s2):
    return float(s1)*float(s2)
    
def getTransform(line):
    if fbx_data['Model:']:
        if fbx_data['Model:'][-1][2]=='"LimbNode"':
            data=last_line.split(',')
            return (fbx_data['Model:'][-1][0], last_line.split(',')[-3:])
    return None    
    
def buildVertexData(index, fbx_data, vertId, rgba, uv, group_name, tbnId=None):
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
    #membership (bone weights)
    membership={}
    for id, cluster in enumerate(fbx_data['Indexes']):
        if str(vertId) in cluster[1]:            
            membership[cluster[0]]= fbx_data['Weights'][id][cluster[1].index(str(vertId))] 
    vert_dict={'xyz':xyz, 'n':n, 't':t, 'b':b, 'rgba':rgba, 'uv':uv, 'group_name':group_name, 'vert_id':tbnId, 'membership':membership}
    return vert_dict
    
in_file=sys.argv[1]
out_file=sys.argv[2]
out_anim_file=None
if len(sys.argv)>3:
    out_anim_file=sys.argv[3]
    
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
        #'Node:':[],#will point to a UI of the matrix that should come next
        #'Matrix':[],
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
        'P: "EmissiveColor"':[], #material emissive
        'P: "Lcl Translation"':[],
        'P: "Lcl Rotation"':[],
        'P: "Lcl Scaling"':[],
        'P: "UpAxis"':[],
        'P: "UpAxisSign"':[],
        'P: "FrontAxis"':[],
        'P: "FrontAxisSign"':[],
        'KeyTime':[]
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
        #'Node:':               lambda x: int(last_line.split(' ')[1]),
        #'Matrix':              lambda x: x.strip('a: ').split(','),
        'Deformer':            lambda x: (last_line.split(',')[0].strip('Deformer: ') if last_line.split(',')[2].strip(' {')=='"Cluster"' else None),
        'Indexes':             lambda x: (fbx_data['Deformer'][-1], x.strip('a: ').split(',')),
        'Weights':             lambda x: x.strip('a: ').split(','),
        'Transform':           lambda x: None,
        'TransformLink':       lambda x: None,
        'Texture:':            lambda x: (last_line.split(',')[0].strip('Texture: '), last_line.split(',')[1].strip('"Texture:: "')),
        'RelativeFilename':    lambda x: (last_line.split(': ')[1].strip('"') if last_line_type=='Texture:' else None),
        'C: ':                 lambda x: (last_line.split(',')),
        'AnimationCurve':      lambda x: last_line.split(',')[0].strip('AnimationCurve: '),
        'KeyValueFloat':       lambda x: (fbx_data['AnimationCurve'][-1], x.strip('a: ').split(',')),
        'Material:':           lambda x: None,
        'P: "DiffuseColor"':   lambda x: None,
        'P: "AmbientColor"':   lambda x: None,
        'P: "SpecularColor"':  lambda x: None,
        'P: "Shininess"':      lambda x: None,
        'P: "EmissiveColor"':  lambda x: None,
        'P: "Lcl Translation"':lambda x: getTransform(last_line),#lambda got too long, made a named function        
        'P: "Lcl Rotation"':   lambda x: getTransform(last_line),
        'P: "Lcl Scaling"':    lambda x: getTransform(last_line),
        'P: "UpAxis"':         lambda x: last_line.strip('P: "UpAxis", "int", "Integer", "",'),
        'P: "UpAxisSign"':     lambda x: last_line.strip('P: "UpAxisSign", "int", "Integer", "",'),
        'P: "FrontAxis"':      lambda x: last_line.strip('P: "FrontAxis", "int", "Integer", ""'),
        'P: "FrontAxisSign"':  lambda x: last_line.strip('P: "FrontAxisSign", "int", "Integer", ""'),
        'KeyTime':             lambda x: last_line.strip('KeyTime: *').strip(' }')
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
            last_line_type=line_type
            line_type=None            
        for key in fbx_data:
            if line.startswith(key):
                line_type=key
        last_line=line 
#data needed to build an egg file
egg_data={'Group':[],#{'name':'', id:''}
          'Vertex':{},#{'xyz':[], 'n':[], 'b':[], 't':[], 'uv':[], 'rgba':[]}
          'Polygon':{},#{'TRef':[],'VertexRef':[], 'id':''}???
          'Joint':[],#{'name:'', 'id':'', 'Transform':[], 'VertexRef':[(vertId,weight)]}???
          'Texture':{},
          'Axis':'Z-Up'
          }
#get the CoordinateSystem
#my exporter only let's me set the axis convetion to either z or y up, no other options
#I won't even try to understand how this works
if (fbx_data['P: "UpAxis"']==['1'] and fbx_data['P: "UpAxisSign"']==['1'] and fbx_data['P: "FrontAxis"']==['2'] and fbx_data['P: "FrontAxisSign"']==['1']):
   egg_data['Axis']='Y-up'
#else:  #the default already set  
#    egg_data['Axis']='Z-up'
        
#find groups and joints
for group in fbx_data['Model:']:
    if group[2]=='"Mesh"':
        egg_data['Group'].append({'name':group[1], 'id':group[0]})
        egg_data['Vertex'][group[0]]=[]
        egg_data['Polygon'][group[0]]=[]
        egg_data['Texture'][group[0]]=[]
    elif group[2]=='"LimbNode"':
        egg_data['Joint'].append({'name':group[1], 'id':group[0], 'verts':[], 'anim':[], 'v':[], 'AnimCurveNode':[]})
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
    egg_data['Texture'][group_id].append({'file':file,
                                        'stage-name':None,
                                        'compression':None,
                                        'anisotropic-degree':None,
                                        'alpha':None,
                                        'format':'rgb', 
                                        'wrapu': 'repeat',
                                        'wrapv': 'repeat', 
                                        'minfilter':'linear_mipmap_linear ', 
                                        'magfilter':'linear', 
                                        'type':type})
    
#joints
#we need the transforms and hierarchy 
#we also get some animation data (this will need another pass)
for index, joint in enumerate(egg_data['Joint']):
    id=joint['id']
    for connection in fbx_data['C: ']:        
        if connection[1]==id:
            #the connection can point to  
            if connection[2]=='0':#-RootNode            
                egg_data['Joint'][index]['parent']=connection[2]            
            elif any(d['id']==connection[2] for d in egg_data['Joint']):#-other bone
                egg_data['Joint'][index]['parent']=connection[2]
            else:#-SubDeformer (weights)
                egg_data['Joint'][index]['deformer']=connection[2]
        if connection[2]==id:        
            if len(connection)==4:#AnimCurveNode  
                egg_data['Joint'][index]['AnimCurveNode'].append((connection[1], connection[3]))
    #get the transformation for the rest pose... or something near it(???)                    
    for translation in fbx_data['P: "Lcl Translation"']:                
        if translation[0]==str(id):
            egg_data['Joint'][index]['translate']=translation[1]
    for rotation in fbx_data['P: "Lcl Rotation"']:
        if rotation[0]==str(id):
            egg_data['Joint'][index]['RotX']=rotation[1][0]
            egg_data['Joint'][index]['RotY']=rotation[1][1]
            egg_data['Joint'][index]['RotZ']=rotation[1][2]
    for scale in fbx_data['P: "Lcl Scaling"']:        
        if scale[0]==str(id):            
            egg_data['Joint'][index]['scale']=scale[1]          
#getting anim type
for index, joint in enumerate(egg_data['Joint']):
    for node in joint['AnimCurveNode']:        
        id=node[0]
        for connection in fbx_data['C: ']:           
            if connection[2]==id:
                if node[1]==' "Lcl Translation"':                    
                    if connection[3]==' "d|X"': 
                        egg_data['Joint'][index]['anim'].append((connection[1],'x'))
                    elif connection[3]==' "d|Y"':
                        egg_data['Joint'][index]['anim'].append((connection[1],'y'))
                    elif connection[3]==' "d|Z"':
                        egg_data['Joint'][index]['anim'].append((connection[1],'z'))
                elif node[1]==' "Lcl Rotation"':
                    if connection[3]==' "d|X"': 
                        egg_data['Joint'][index]['anim'].append((connection[1],'h'))
                    elif connection[3]==' "d|Y"':
                        egg_data['Joint'][index]['anim'].append((connection[1],'r'))
                    elif connection[3]==' "d|Z"':
                        egg_data['Joint'][index]['anim'].append((connection[1],'p'))
                elif node[1]==' "Lcl Scaling"':
                    if connection[3]==' "d|X"': 
                        egg_data['Joint'][index]['anim'].append((connection[1],'i'))
                    elif connection[3]==' "d|Y"':
                        egg_data['Joint'][index]['anim'].append((connection[1],'j'))
                    elif connection[3]==' "d|Z"':
                        egg_data['Joint'][index]['anim'].append((connection[1],'k'))
                for value in fbx_data['KeyValueFloat']:
                    if value[0]==connection[1]:
                        egg_data['Joint'][index]['v'].append(value)

#fill the anims with empty values where needed
for index, joint in enumerate(egg_data['Joint']): 
    joint['v'].append(('0',[0]))
    joint['v'].append(('1',[1]))
    needed0=['x','y','z','h', 'p', 'r']
    needed1=['i', 'j', 'k']
    for anim in joint['anim']:
        for type in needed0:
            if type in anim:
                needed0.pop(needed0.index(type))
        for type in needed1:
            if type in anim:
                needed1.pop(needed0.index(type))        
    for type in needed0:    
        joint['anim'].append(('0', type))
    for type in needed1:    
        joint['anim'].append(('1', type))    
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
                vert_dict=buildVertexData(index, fbx_data, vertId, temp_color, temp_uv,group['name'])
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
                vert_dict=buildVertexData(index, fbx_data, vertId, temp_color, temp_uv, group['name'], id)
                egg_data['Vertex'][group['id']].append(vert_dict)
                new_poly.append(id) 
                id+=1
            egg_data['Polygon'][group['id']].append(new_poly) 

#At this point we have the vertex membership (weights) in the  egg_data['Vertex'][group_id][vert_id]['membership']
#but for the egg we need to have the heights per joint with info in what VertexPool the vert is at
for joint in egg_data["Joint"]:
    if 'deformer' in joint:
        deformer_id=joint['deformer']
        for group in egg_data['Vertex']:
            for vert in egg_data['Vertex'][group]:        
                if deformer_id in vert['membership']:                
                    joint['verts'].append({'vert_id':vert['vert_id'],
                                          'membership':vert['membership'][deformer_id],
                                          'group':vert['group_name']})
#write the egg file   
with open(out_file,'w') as egg:
    egg.write('<CoordinateSystem> {{ {Axis} }}\n\n'.format(**egg_data))
    #Textures
    for tex in egg_data['Texture']:
        for index, temp in enumerate(egg_data['Texture'][tex]):        
            egg.write('<Texture> Tex{0} {{\n'.format(index))
            egg.write('    {file}\n'.format(**egg_data['Texture'][tex][index]))
            #TODO: this should be set in the GUI.. once a GUI exist
            egg.write('    <Scalar> format {{ {format} }}\n'.format(**egg_data['Texture'][tex][index]))
            egg.write('    <Scalar> wrapu {{ {wrapu} }}\n'.format(**egg_data['Texture'][tex][index]))
            egg.write('    <Scalar> wrapv {{ {wrapv} }}\n'.format(**egg_data['Texture'][tex][index]))
            egg.write('    <Scalar> minfilter {{ {minfilter} }}\n'.format(**egg_data['Texture'][tex][index]))
            egg.write('    <Scalar> magfilter {{ {magfilter} }}\n'.format(**egg_data['Texture'][tex][index]))
            egg.write('    <Scalar> envtype {{ {type} }}\n'.format(**egg_data['Texture'][tex][index]))
            if egg_data['Texture'][tex][index]['stage-name']:
                egg.write('    <Scalar> stage-name {{ {stage-name} }}\n'.format(**egg_data['Texture'][tex][index]))
            if egg_data['Texture'][tex][index]['compression']:
                egg.write('    <Scalar> compression {{ {compression} }}\n'.format(**egg_data['Texture'][tex][index]))
            if egg_data['Texture'][tex][index]['anisotropic-degree']:
                egg.write('    <Scalar> anisotropic-degree {{ {anisotropic-degree} }}\n'.format(**egg_data['Texture'][tex][index])) 
            if egg_data['Texture'][tex][index]['alpha']:
                egg.write('    <Scalar> alpha {{ {alpha} }}\n'.format(**egg_data['Texture'][tex][index]))                
            egg.write('}\n')
    #a group of all groups             
    if egg_data['Joint']:
        #the 3ds max exporter names all animated object 'character'
        #testing with an animation exported from there so I'll do the same
        egg.write('<Group> character {\n') 
        egg.write('<Dart> { 1 }\n')
    else:    
        egg.write('<Group> SceneRoot {\n')
    for index, group in enumerate(egg_data['Group']):            
        #group
        egg.write('<Group> {name} {{\n'.format(**group))
        #vertex pool
        egg.write('    <VertexPool> {name}.verts {{\n'.format(**group))
        for id, vertex in enumerate(egg_data['Vertex'][group['id']]):
            v_data=egg_data['Vertex'][group['id']][id]
            egg.write('        <Vertex> {0} {{\n'.format(id))
            egg.write('        {xyz[0]} {xyz[1]} {xyz[2]}\n'.format(**v_data))
            #normal, color, uv, tb could be missing
            if v_data['n']:    
                egg.write('            <Normal> {{ {n[0]} {n[1]} {n[2]} }}\n'.format(**v_data))
            if v_data['rgba']:    
                egg.write('            <RGBA> {{ {rgba[0]} {rgba[1]} {rgba[2]} {rgba[3]} }}\n'.format(**v_data))
            if v_data['uv']:
                egg.write('            <UV> {\n')
                egg.write('                {uv[0]} {uv[1]}\n'.format(**v_data))   
                if v_data['t']:   
                    egg.write('                <Tangent> {{ {t[0]} {t[1]} {t[2]} }}\n'.format(**v_data))
                if v_data['b']:    
                    egg.write('                <Binormal> {{ {b[0]} {b[1]} {b[2]} }}\n'.format(**v_data))
                egg.write('            }\n')            
            egg.write('        }\n')
        egg.write('    }\n')    
        #polygons    
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
        egg.write('}\n')
    #one actor per file!
    if egg_data['Joint']:
        next_joint_id='0'
        indent=''
        joint_order=[]
        while any(d['parent']==next_joint_id for d in egg_data['Joint']):
            for joint in egg_data['Joint']:
                if joint['parent']==next_joint_id:
                    egg.write(indent+'<Joint> {name} {{\n'.format(**joint)) 
                    egg.write(indent+'    <Transform> {\n')
                    if 'translate' in joint:
                        egg.write(indent+'        <Translate> {{ {translate[0]} {translate[1]} {translate[2]} }}\n'.format(**joint))
                    if 'RotX' in joint:
                        egg.write(indent+'        <RotX> {{ {RotX} }} \n'.format(**joint))
                    if 'RotY' in joint:
                        egg.write(indent+'        <RotY> {{ {RotY} }} \n'.format(**joint))
                    if 'RotZ' in joint:
                        egg.write(indent+'        <RotZ> {{ {RotZ} }} \n'.format(**joint))
                    if 'scale' in joint:
                        egg.write(indent+'        <Scale> {{ {scale[0]} {scale[1]} {scale[2]} }}\n'.format(**joint))  
                    egg.write(indent+'        }\n')
                    next_joint_id=joint['id']
                    indent+='    '
                    joint_order.append(joint['id'])
        for joint_id in reversed(joint_order):
            for joint in egg_data['Joint']:
                if joint['id']==joint_id:
                    indent=indent[:-4]                    
                    for verts in joint['verts']:
                        egg.write(indent+'    <VertexRef> {\n')
                        egg.write(indent+'    {vert_id}\n'.format(**verts))
                        egg.write(indent+'        <Scalar> membership {{ {membership} }}\n'.format(**verts))
                        egg.write(indent+'        <Ref> {{ {group}.verts }}\n'.format(**verts))
                        egg.write(indent+'    }\n')                
            egg.write(indent+'}\n')        
    egg.write('}')#close the SceneRoot group
    
#write the egg animation file   
if out_anim_file:
    with open(out_anim_file,'w') as egg:  
        egg.write('<CoordinateSystem> {{ {Axis} }}\n\n'.format(**egg_data))
        egg.write('<Table> {\n')
        egg.write('    <Bundle> character {\n')
        egg.write('        <Table> "<skeleton>" {\n')
        if egg_data['Joint']:
            next_joint_id='0'
            indent='            '
            joint_order=[]
            while any(d['parent']==next_joint_id for d in egg_data['Joint']):
                for joint in egg_data['Joint']:
                    if joint['parent']==next_joint_id:
                        egg.write(indent+'<Table> {name} {{\n'.format(**joint))
                        egg.write(indent+'    <Xfm$Anim_S$> xform {\n')
                        egg.write(indent+'        <Scalar> fps { 30 }\n') #TODO: calculate the fps in the fbx..but how?
                        egg.write(indent+'        <Char*> order { srpht }\n')#no idea how to get this data :(
                        for anim in joint['anim']:
                            egg.write(indent+'        <S$Anim> {0} {{\n'.format(anim[1]))#not in a dict this time
                            egg.write(indent+'            <V> {')                            
                            #transfor of the joint neede
                            if next_joint_id!='0':
                                transform=0.0
                                f=add
                                if anim[1]=="x" and 'translate' in joint:
                                    transform=joint['translate'][0]
                                elif anim[1]=="y" and 'translate' in joint:
                                    transform=joint['translate'][1]
                                elif anim[1]=="z" and 'translate' in joint:
                                    transform=joint['translate'][2]
                                elif anim[1]=="h" and 'RotX' in joint:
                                    transform=joint['RotX']
                                elif anim[1]=="r" and 'RotY' in joint:
                                    transform=joint['RotY']  
                                elif anim[1]=="p" and 'RotZ' in joint:
                                    transform=joint['RotZ']  
                                elif anim[1]=="i" and 'scale' in joint:
                                    transform= joint['scale'][0] 
                                    f=mul
                                elif anim[1]=="j" and 'scale' in joint:
                                    transform= joint['scale'][1]   
                                    f=mul
                                elif anim[1]=="k" and 'scale' in joint:
                                    transform= joint['scale'][2]                               
                                    f=mul
                                for v in joint['v']:
                                    if v[0]==anim[0]:                                    
                                        for s in v[1]:
                                            egg.write(str(f(s, transform))+" ")
                            else:                
                                for v in joint['v']:
                                    if v[0]==anim[0]:                                    
                                        for s in v[1]:
                                            egg.write(str(s)+" ")
                            egg.write('}\n')    
                            egg.write(indent+'        }\n')
                        egg.write(indent+'    }\n')   
                    indent+='    '
                    joint_order.append(joint['id'])                    
                    next_joint_id=joint['id']
            for joint_id in joint_order:
                indent=indent[:-4] 
                egg.write(indent+'}\n')
            egg.write('        }\n')
            egg.write('    }\n')
            egg.write('}\n')    