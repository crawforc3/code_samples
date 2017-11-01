# Pull and clean data from the Dark Sky API

# Fresh start
rm(list=ls())

# Load libraries
require("darksky")
require("RCurl")
require("jsonlite")
require("lubridate")
require("plyr")


# fake latitude and longitude
lat <- "34.608013"
lon <- "-225.335167"


# Set Dark Sky API key (deleted for privacy)
DARKSKY_API_KEY = "123456meowmeow"


# Get the dates for the number of days of data
listofdates <- NULL
numdays <- 1000
  for (i in 1:numdays){
  listofdates <- append(x = listofdates, values = date-i)
  }


# Prepare storage
write_all <- NULL
write_hourly <- NULL
write_daily <- NULL
df_all <- NULL
df_hourly <- NULL
df_daily <- NULL


# Iterate through list and do an API call for each
for (i in 1:length(listofdates)){
  
  possibleError <- tryCatch({
    #Convert to UNIX time for API
    UNIXtime <- as.integer(as.POSIXct(listofdates[i]))
    
    # Create/fetch the URL
    root <- "https://api.darksky.net/forecast/61a2d6918220167e170b57fb3720a932/" 
    u <- paste(root, lat, "," ,lon, "," , UNIXtime, "?exclude=currently,flags", sep = "")
    url <- URLencode(u)
    
    # Parse the response
    json <- getURL(url)
    simple <- fromJSON(txt = json, simplifyDataFrame = TRUE, flatten = TRUE)
    all <- simple
    hourly <- simple$hourly
    daily <- simple$daily
    
    # Convert UNIX time to datetime
    time <- lapply(hourly$data["time"], as_datetime, tz = Sys.timezone())
    
    # Diagnostic print statements
    print(paste("Iteration: ",i))
    #print(names(hourly$data))
    #print(names(daily$data))
    
    df_hourly <- data.frame( Time = time, hourly$data, check.rows = FALSE )
    write_hourly <- rbind.fill(write_hourly, df_hourly)
    write.csv( write_hourly, file="../Research\ project/10khours.csv", row.names = FALSE, append = TRUE )

    df_daily <- data.frame( daily$data, check.rows = FALSE )
    write_daily <- rbind.fill(write_daily, df_daily)
    write.csv( write_daily, file="../Research\ project/10kdays.csv", row.names = FALSE, append = TRUE )
    
    
  }, error = function(err) {
    err
    # error handler picks up where error was generated
    print(paste("Iteration:", i,"MY_ERROR:", err))
  })
  
  if(inherits(possibleError, "error")) next
  
}
  




