import os, sys

in_file=sys.argv[1]
out_file=sys.argv[2]

#data needed to construct an egg
#geometry
group=[]
vertex=[]
tangent=[]
binormal=[]
normal=[]
polygon=[]
uv=[]
uv_index=[]
texture=[]
weight=[]
joint=[]

isVertex=False
isTangent=False
isBinormal=False
isNormal=False
isPolygon=False
isUV=False
isUVIndex=False

#read the fbx file
with open(in_file,'r') as fbx:
    for line in fbx:
        if isVertex:
            vertex.append(line.strip('a: ').strip('\n').split(','))
            isVertex=False
        elif isPolygon:
            polygon.append(line.strip('a: ').strip('\n').split(','))
            isPolygon=False   
        elif isNormal:
            normal.append(line.strip('a: ').strip('\n').split(','))
            isNormal=False  
        elif isBinormal:
            binormal.append(line.strip('a: ').strip('\n').split(','))
            isBinormal=False
        elif isTangent:
            tangent.append(line.strip('a: ').strip('\n').split(','))
            isTangent=False
        elif isUV:
            uv.append(line.strip('a: ').strip('\n').split(','))
            isUV=False
        elif isUVIndex:
            uv_index.append(line.strip('a: ').strip('\n').split(','))
            isUVIndex=False
            
        if line.strip().startswith('Model:') and line.strip().endswith('"Mesh" {'):
            temp=line.strip().split(',')
            #should be ['Model/Geometry: {some_number}', '"Model::{some_name}"', '"Mesh" {']
            group.append((temp[0].strip('Model: '), temp[1].strip('"Model:: "')))
        elif line.strip().startswith('Vertices'):
            isVertex=True
        elif line.strip().startswith('PolygonVertexIndex'):
            isPolygon=True
        elif line.strip().startswith('Normals'):
            isNormal=True    
        elif line.strip().startswith('Binormals'):
            isBinormal=True 
        elif line.strip().startswith('Tangents'):
            isTangent=True  
        elif line.strip().startswith('UV:'):
            isUV=True  
        elif line.strip().startswith('UVIndex:'):
            isUVIndex=True 
            
         
#convert the fbx data to egg data  
egg_data={}
index=0
for gr in group:
    egg_vertex=[]
    egg_poly=[]
    temp_poly=[]
    temp_uv=[]
    poly=[]
    #build a list of polygons
    #the verts are wrong for now - or right if there are no normals and uv :( 
    for v in polygon[index]:
        if int(v)>-1:
            poly.append(v)
        else:
            poly.append(int(v)*(-1)-1)
            temp_poly.append(poly)
            poly=[]
    #we need uv for each vert not some funky index        
    for i in uv_index[index]:       
        temp_uv.append((uv[index][int(i)*2],uv[index][int(i)*2+1]))        
    
    # I was thinking I'd need to remove duplicated verts
    # but I don't - if I do all is mixed up        
    #TODO: rewrite this part of the code to be more sane
    id=0   
    for polygon in temp_poly:
        new_poly=[]
        for vertId in polygon:            
            vert=(vertex[index][int(vertId)*3],vertex[index][int(vertId)*3+1],vertex[index][int(vertId)*3+2])
            norm=(normal[index][id],normal[index][id+1],normal[index][id+2])
            #TODO: check if there are any tbn!!
            tang=(tangent[index][id],tangent[index][id+1],tangent[index][id+2])
            bino=(binormal[index][id],binormal[index][id+1],binormal[index][id+2])
            uv=temp_uv[int(vertId)]
            egg_vertex.append((vert, norm, tang, bino, uv))
            new_poly.append(egg_vertex.index((vert, norm, tang, bino,uv)))           
            id+=3
        egg_poly.append(new_poly)    
    
    egg_data[gr[1]]={'vertex':egg_vertex,
                    'poly':egg_poly
                    } 
    index+=1                        
#write the egg file    
with open(out_file,'w') as egg:
    egg.write('<CoordinateSystem> { Z-Up }\n\n')
    for group in egg_data:
        egg.write('<Group> '+group+' {\n')
        egg.write('    <VertexPool> '+group+'.verts {\n')
        i=0
        for v in egg_data[group]['vertex']: 
            egg.write('        <Vertex> '+str(i)+' {\n')
            egg.write('        '+'{0} {1} {2}'.format(*v[0])+'\n')
            egg.write('            <Normal> {'+'{0} {1} {2}'.format(*egg_data[group]['vertex'][i][1])+'}\n')
            egg.write('            <UV> {\n')
            egg.write('                {0} {1}\n'.format(*egg_data[group]['vertex'][i][4]))
            if tangent:
                egg.write('                <Tangent> {'+'{0} {1} {2}'.format(*egg_data[group]['vertex'][i][2])+'}\n')
                egg.write('                <Binormal> {'+'{0} {1} {2}'.format(*egg_data[group]['vertex'][i][3])+'}\n')
            egg.write('            }\n')
            egg.write('        }\n')
            i+=1
        egg.write('    }\n')
        for v in egg_data[group]['poly']:
            egg.write('    <Polygon> {\n')
            egg.write('    <VertexRef> { ')
            for n in v:
                egg.write(str(n)+" ")
            egg.write(' <Ref> { '+group+'.verts } }\n')
            egg.write('    }\n')
        egg.write('}')    
     
    