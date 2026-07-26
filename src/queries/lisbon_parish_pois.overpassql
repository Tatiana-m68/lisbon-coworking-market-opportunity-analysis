[out:json][timeout:180];
(
  nwr["office"](38.680,-9.250,38.820,-9.070);
  nwr["amenity"="cafe"](38.680,-9.250,38.820,-9.070);
  nwr["tourism"="hotel"](38.680,-9.250,38.820,-9.070);
  nwr["amenity"="university"](38.680,-9.250,38.820,-9.070);
  nwr["amenity"="college"](38.680,-9.250,38.820,-9.070);
  nwr["railway"~"station|halt|tram_stop"](38.680,-9.250,38.820,-9.070);
  nwr["station"="subway"](38.680,-9.250,38.820,-9.070);
  nwr["highway"="bus_stop"](38.680,-9.250,38.820,-9.070);
  nwr["public_transport"="station"](38.680,-9.250,38.820,-9.070);
);
out center tags;
