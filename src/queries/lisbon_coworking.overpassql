[out:json][timeout:90];
(
  nwr["office"="coworking"](38.680,-9.250,38.820,-9.070);
  nwr["amenity"="coworking_space"](38.680,-9.250,38.820,-9.070);
  nwr["office"="coworking_space"](38.680,-9.250,38.820,-9.070);
  nwr["name"~"cowork|co-work|co work",i](38.680,-9.250,38.820,-9.070);
  nwr["name"~"escrit[oó]rio(s)? partilhado(s)?|espa[cç]o(s)? de trabalho partilhado(s)?",i](38.680,-9.250,38.820,-9.070);
);
out center tags;
