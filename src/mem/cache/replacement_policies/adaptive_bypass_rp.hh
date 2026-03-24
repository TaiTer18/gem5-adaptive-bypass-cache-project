#ifndef __MEM_CACHE_REPLACEMENT_POLICIES_ADAPTIVE_BYPASS_RP_HH__
#define __MEM_CACHE_REPLACEMENT_POLICIES_ADAPTIVE_BYPASS_RP_HH__

#include "base/types.hh"
#include "mem/cache/replacement_policies/base.hh"
#include "base/statistics.hh"

struct AdaptiveBypassRPParams;

class AdaptiveBypassRP : public BaseReplacementPolicy
{
  protected:
    /** Adaptive Bypassing custom statistics */
    struct AdaptiveBypassStats : public Stats::Group
    {
        AdaptiveBypassStats(Stats::Group *parent);

        /** Number of total bypasses made */
        Stats::Scalar totalBypasses;

        /** Number of bypasses that correctly skipped non-reused blocks */
        Stats::Scalar effectiveBypasses;

        /** Number of bypasses that incorrectly skipped blocks later requested */
        Stats::Scalar ineffectiveBypasses;

        /** Number of hypothetical bypasses that correctly predicted a block would not be reused */
        Stats::Scalar virtualEffectiveBypasses;

        /** Number of hypothetical bypasses that incorrectly predicted a block would not be reused */
        Stats::Scalar virtualIneffectiveBypasses;
    };
    
    AdaptiveBypassStats stats;

    /** Adaptive Bypass specific implementation of replacement data. */
    struct AdaptiveBypassReplData : ReplacementData
    {
        /** Tick on which the entry was last touched. */
        Tick lastTouchTick;

        /** Default constructor. Invalidate data. */
        AdaptiveBypassReplData() : lastTouchTick(0) {}
    };

    /** Initial probability for bypassing */
    const uint8_t initialBypassProbability;
    
    /** Current probability to bypass a line (0-100). */
    mutable unsigned currentBypassProbability;

  public:
    /** Convenience typedef. */
    typedef AdaptiveBypassRPParams Params;

    /**
     * Construct and initialize this replacement policy.
     */
    AdaptiveBypassRP(const Params *p);

    /**
     * Destructor.
     */
    ~AdaptiveBypassRP() {}

    /** Increase bypass probability upon a good bypass. */
    void increaseBypassProb() const;

    /** Decrease bypass probability upon a bad bypass. */
    void decreaseBypassProb() const;

    /**
     * Increment the total block bypasses stat.
     */
    void recordBypass() { stats.totalBypasses++; }

    /**
     * Increment the effective bypasses stat.
     */
    void recordEffectiveBypass() { stats.effectiveBypasses++; }

    /**
     * Increment the ineffective bypasses stat.
     */
    void recordIneffectiveBypass() { stats.ineffectiveBypasses++; }

    /**
     * Increment the virtual effective bypasses stat.
     */
    void recordVirtualEffectiveBypass() { stats.virtualEffectiveBypasses++; }

    /**
     * Increment the virtual ineffective bypasses stat.
     */
    void recordVirtualIneffectiveBypass() { stats.virtualIneffectiveBypasses++; }

    /**
     * Determine if a block should bypass the cache.
     * @return true if bypassed.
     */
    bool shouldBypass() const;

    /** Virtual bypass probability percentage (e.g. 5 means 5%) */
    const int virtualBypassProbability = 5;

    /**
     * Determine if a block should be virtually bypassed.
     * @return true if virtual bypass should be recorded.
     */
    bool shouldVirtualBypass() const;

    /**
     * Invalidate replacement data to set it as the next probable victim.
     *
     * @param replacement_data Replacement data to be invalidated.
     */
    void invalidate(const std::shared_ptr<ReplacementData>& replacement_data) const override;

    /**
     * Touch an entry to update its replacement data.
     *
     * @param replacement_data Replacement data to be touched.
     */
    void touch(const std::shared_ptr<ReplacementData>& replacement_data) const override;

    /**
     * Reset replacement data. Used when an entry is inserted.
     *
     * @param replacement_data Replacement data to be reset.
     */
    void reset(const std::shared_ptr<ReplacementData>& replacement_data) const override;

    /**
     * Find replacement victim using LRU timestamps.
     *
     * @param candidates Replacement candidates, selected by indexing policy.
     * @return Replacement entry to be replaced.
     */
    ReplaceableEntry* getVictim(const ReplacementCandidates& candidates) const override;

    /**
     * Instantiate a replacement data entry.
     *
     * @return A shared pointer to the new replacement data.
     */
    std::shared_ptr<ReplacementData> instantiateEntry() override;
};

#endif // __MEM_CACHE_REPLACEMENT_POLICIES_ADAPTIVE_BYPASS_RP_HH__
