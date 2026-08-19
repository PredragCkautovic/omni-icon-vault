figma.showUI(__html__,{width:460,height:680,themeColors:true});
const API='http://localhost:17836';
function center(node){const c=figma.viewport.center;node.x=c.x-node.width/2;node.y=c.y-node.height/2}
async function insertIcon(icon,size){size=Math.max(8,Math.min(Number(size)||24,512));let node;
  if(icon.svg){node=figma.createNodeFromSvg(icon.svg);const max=Math.max(node.width||1,node.height||1),scale=size/max;node.resize(Math.max(1,node.width*scale),Math.max(1,node.height*scale));}
  else if(icon.raster){const image=await figma.createImageAsync(API+icon.raster);node=figma.createRectangle();node.resize(size,size);node.fills=[{type:'IMAGE',scaleMode:'FIT',imageHash:image.hash}];}
  else if(icon.char){const family=icon.fontFamily||(icon.source==='material'?'Material Symbols Outlined':'Symbols Nerd Font Mono'),style=icon.fontStyle||'Regular',font={family,style};try{await figma.loadFontAsync(font)}catch(err){figma.notify(`Font not available: ${family}. Restart Figma after installing Omni fonts.`,{error:true,timeout:6000});throw err}node=figma.createText();node.fontName=font;node.fontSize=size;node.characters=icon.char;node.textAutoResize='WIDTH_AND_HEIGHT';}
  else throw new Error('Icon has no SVG, raster asset, or font glyph.');
  node.name=`Icon / ${icon.label||icon.name}`;node.setPluginData('omniIconId',icon.id||'');node.setPluginData('omniIconSource',icon.source||'');center(node);figma.currentPage.selection=[node];figma.viewport.scrollAndZoomIntoView([node]);return node;
}
figma.ui.onmessage=async msg=>{if(!msg||!msg.type)return;if(msg.type==='insert'){try{await insertIcon(msg.icon,msg.size);figma.ui.postMessage({type:'inserted',id:msg.icon&&msg.icon.id})}catch(err){figma.ui.postMessage({type:'error',message:String(err?.message||err)})}}if(msg.type==='close')figma.closePlugin()};
