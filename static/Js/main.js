var notyf = new Notyf({duration:10000,ripple:false, dismissible:true});
var notyf2 = new Notyf({duration:30000,ripple:false, dismissible:true});
function toggle(){
    const notification = notyf.success('Processing image ...');
}
function togglelong(){
    setTimeout( function(){
        const notification = notyf2.success('Processing image ...');
    },3000)
}
