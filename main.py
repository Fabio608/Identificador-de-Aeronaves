flowchart LR
  S(["Start"]) --> P1["Open App"]
  P1["Open App"] --> P2["Configure Flightradar Connection"]
  P2["Configure Flightradar Connection"] --> P3["Enter Credentials Or Api Key"]
  P3["Enter Credentials Or Api Key"] --> D1{"Authentication Successful"}
  D1{"Authentication Successful"} -->|No| P4["Show Error And Log Attempt"]
  P4["Show Error And Log Attempt"] --> P5["Retry Or Update Credentials"]
  P5["Retry Or Update Credentials"] --> P3["Enter Credentials Or Api Key"]
  D1{"Authentication Successful"} -->|Yes| P6["Load User Profile And Entitlements"]
  P6["Load User Profile And Entitlements"] --> P7["Open Mis Aeronaves"]
  P7["Open Mis Aeronaves"] --> P8["Add Or Import Aircraft List"]
  P8["Add Or Import Aircraft List"] --> P9["Validate Registration Format"]
  P9["Validate Registration Format"] --> D2{"Registration Valid"}
  D2{"Registration Valid"} -->|No| P10["Reject Entry And Prompt Fix"]
  P10["Reject Entry And Prompt Fix"] --> P8["Add Or Import Aircraft List"]
  D2{"Registration Valid"} -->|Yes| P11["Save Aircraft To List"]
  P11["Save Aircraft To List"] --> P12["Open Flight Tracker"]
  P12["Open Flight Tracker"] --> P13["Select Aircraft And Date Range"]
  P13["Select Aircraft And Date Range"] --> P14["Query Flight History"]
  P14["Query Flight History"] --> D3{"Flights Found"}
  D3{"Flights Found"} -->|No| P15["Show No Results And Adjust Filters"]
  P15["Show No Results And Adjust Filters"] --> P13["Select Aircraft And Date Range"]
  D3{"Flights Found"} -->|Yes| P16["Display Flight Events Timeline"]
  P16["Display Flight Events Timeline"] --> P17["Select Flight Segment"]
  P17["Select Flight Segment"] --> P18["Request Track Data"]
  P18["Request Track Data"] --> D4{"KMZ Export Available"}
  D4{"KMZ Export Available"} -->|No| P19["Show Export Not Available"]
  P19["Show Export Not Available"] --> E(["End"])
  D4{"KMZ Export Available"} -->|Yes| P20["Download KMZ And Save Metadata"]
  P20["Download KMZ And Save Metadata"] --> E(["End"])
