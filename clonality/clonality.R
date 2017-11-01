# Clonality.R
# This script reads in a data file that contains scraped and cleaned values.
# Statistics are run on the data values and the script generates a report.

# Clean start
rm(list=ls())

# Load Dunn test
library(dunn.test)


CalculateUTest <- function() {
  # Return results of U-test/Mann-whitney/Wilcoxon
  Uout = wilcox.test(data_raw[,metric] ~ data_raw[,factor])
  u_df <- data.frame(Test = "utest", MultipleCorrection = "N/A", comparison = comparison_groups, pvalue = Uout$p.value, significant = Uout$p.value<0.05)
  return(u_df)
}


CalculateDunnTest <- function(correction='none') {
  # Return results of Dunn's test
  dunn = dunn.test(data_raw[,metric], data_raw[, factor], method=correction)
  dunn_df <- data.frame(test = "dunntest", MultipleCorrection = correction, comparison = dunn$comparisons, pvalue = dunn$P.adjusted, significant = dunn$P.adjusted < 0.05)
  return(dunn_df)
}


CalculateSummaryStatistics <- function() {
  # Returns summary statistics, standard deviation, and standard error of the mean as a list
  
  # Summary stats on data
  summary <- aggregate(Value~Group, data_raw, summary)
  
  # Standard devation
  sd <- aggregate(Value~Group, data_raw, sd)
  
  # Standard error of mean
  len <- aggregate(Value~Group, data_raw, length)
  denominator <- aggregate(Value~Group, len, sqrt)
  SEM <- data.frame(Group = sd[,1], SEM = (sd[,2]/denominator[,2]))
  
  summaryList <- list("summary"=summary, "sd"=sd, "SEM"=SEM)
  
  return(summaryList)
}


RunStats <- function() {
  # Determine the number of grouped samples and return either U-test or Dunn's test results.
  if (length(levels(data_raw$Group)) == 2) {
    # U-test
    statistic = CalculateUTest()
    
    return(statistic)
    
  } else if (length(levels(data_raw$Group)) > 2) {
    # Dunn's test, check verbosity of output
    if (verbose == FALSE) {
      # Calculate with correctionMethod only
      statistic <- CalculateDunnTest(MultipleCorrection = correctionMethod)
    } else if (verbose == TRUE) {
      # Calculate with all correction methods
      dunn_uncorrected <- CalculateDunnTest("none")
      dunn_bonferroni <- CalculateDunnTest("bonferroni")
      dunn_bh <- CalculateDunnTest("bh")
      # Combine everything into one dataframe
      statistic <- rbind(dunn_uncorrected, dunn_bh,dunn_bonferroni)
    }
    return(statistic)
  }
}


# Load the raw data into dataframes
csv_raw_data <- read.csv(file="pre_stats.tsv", header=TRUE, sep="\t")
data_raw <- data.frame("#data:", csv_raw_data[1:2])

# Load all of the data points for reproducibility
csv_reproducible <- read.csv(file="pre_repro.tsv", header=TRUE, sep="\t")
data_repro <- data.frame("#data:", csv_reproducible[1:3])

# Parse the data type
data_type = names(csv_raw_data[3])

# Parse the correction method
correctionMethod = names(csv_raw_data[4])

# Parse the output verbosity
verbose = as.logical(names(csv_raw_data[5]))

# Variables for tests
metric = 'Value'
factor = 'Group'
group_names <- unique(data_raw["Group"])
comparison_groups <- paste(as.character(group_names[1,1]), '-', as.character(group_names[2,1]))

# Build the output filename
filename = paste("post_stats_", data_type,".tsv", sep='')

# Build the output file headers
# Summary statistics
summary_header = c("#SUMMARYgroup", "#SUMMARYmin", "#SUMMARY1stquartile","#SUMMARYmedian", "#SUMMARYmean", "#SUMMARY3rdquartile", "#SUMMARYmax")
# Standard deviation
sd_header = c("#SDgroup", "#SDvalue")
# Stadard error of the mean
SEM_header = c("#SEMgroup", "#SEMvalue")
# Utest/Dunn test
stats_header = c("#test", "#multiplecorrection", "#comparisongroups", "#pvalue", "#significant")

# Do the tests
statistic <- RunStats()
summaryList <- CalculateSummaryStatistics()

# Writing results to file
write.table(noquote(t(summaryList$summary)), file = noquote(filename), sep="\t", eol="\n", row.names = summary_header, col.names = FALSE, append = TRUE)
write.table(noquote(t(summaryList$sd)), file = noquote(filename), sep="\t", eol="\n", row.names = sd_header, col.names = FALSE, append = TRUE)
write.table(noquote(t(summaryList$SEM)), file = noquote(filename), sep="\t", eol="\n", row.names = SEM_header, col.names=FALSE, append = TRUE)
write.table(noquote(statistic), file = noquote(filename), sep="\t", eol="\n", row.names=FALSE, col.names=stats_header, append = TRUE)
write.table(noquote(data_repro), file = noquote(filename), sep ="\t", eol="\n", row.names = FALSE, col.names = FALSE, append=TRUE)

