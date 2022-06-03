window.parseISOString = function parseISOString(s) {
  var b = s.split(/\D+/);
  return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};

	function deleteVenueFunction(venue_id) {
    fetch(`/venues/${venue_id}`, {
        method: "DELETE"
    }).then(function(response){
        if (response.redirected) {
            window.location.href=response.url
        }
    }).catch(function(error){
        console.log(error)
    })
}