#include "mem/cache/replacement_policies/adaptive_bypass_rp.hh"

#include <cassert>
#include <memory>

#include "base/random.hh"
#include "params/AdaptiveBypassRP.hh"
#include "sim/core.hh"
#include "base/statistics.hh"


AdaptiveBypassRP::AdaptiveBypassRP(const Params *p)
  : BaseReplacementPolicy(p),
    stats(this),
    initialBypassProbability(p->initial_bypass_probability),
    currentBypassProbability(p->initial_bypass_probability)
{
}

AdaptiveBypassRP::AdaptiveBypassStats::AdaptiveBypassStats(
    Stats::Group *parent)
    : Stats::Group(parent),
      ADD_STAT(totalBypasses, "Total number of cache bypasses"),
      ADD_STAT(effectiveBypasses, "Bypasses that correctly skipped non-reused blocks"),
      ADD_STAT(ineffectiveBypasses, "Bypasses that incorrectly skipped requested blocks"),
      ADD_STAT(virtualEffectiveBypasses, "Virtual bypasses correctly predicting non-reused blocks"),
      ADD_STAT(virtualIneffectiveBypasses, "Virtual bypasses incorrectly predicting requested blocks")
{
}

void AdaptiveBypassRP::increaseBypassProb() const {

    if (currentBypassProbability == 0) {
        currentBypassProbability = 5; // Prevent getting stuck at 0 forever
    } else {
        currentBypassProbability += (currentBypassProbability / 2);
    }
    if (currentBypassProbability > 100) {
        currentBypassProbability = 100;
    }
}

void AdaptiveBypassRP::decreaseBypassProb() const {
    currentBypassProbability -= (currentBypassProbability / 2);
}

bool AdaptiveBypassRP::shouldBypass() const {
    if (currentBypassProbability == 0) return false;
    unsigned rand_num = random_mt.random<unsigned>(0, 100);
    return rand_num < currentBypassProbability;
}

bool AdaptiveBypassRP::shouldVirtualBypass() const {

    // Never virutal bypass if bypass proability is >= 20%
    if (currentBypassProbability >= 20) return false;

    unsigned rand_num = random_mt.random<unsigned>(0, 100);
    return rand_num < virtualBypassProbability;
}

void
AdaptiveBypassRP::invalidate(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // Reset last touch timestamp
    std::static_pointer_cast<AdaptiveBypassReplData>(
        replacement_data)->lastTouchTick = Tick(0);
}

void
AdaptiveBypassRP::touch(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // Update last touch timestamp
    std::static_pointer_cast<AdaptiveBypassReplData>(
        replacement_data)->lastTouchTick = curTick();
}

void
AdaptiveBypassRP::reset(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // Set last touch timestamp
    std::static_pointer_cast<AdaptiveBypassReplData>(
        replacement_data)->lastTouchTick = curTick();
}

ReplaceableEntry*
AdaptiveBypassRP::getVictim(const ReplacementCandidates& candidates) const
{
    // There must be at least one replacement candidate
    assert(candidates.size() > 0);

    // Visit all candidates to find victim
    ReplaceableEntry* victim = candidates[0];
    for (const auto& candidate : candidates) {
        // Update victim entry if necessary
        if (std::static_pointer_cast<AdaptiveBypassReplData>(
                    candidate->replacementData)->lastTouchTick <
                std::static_pointer_cast<AdaptiveBypassReplData>(
                    victim->replacementData)->lastTouchTick) {
            victim = candidate;
        }
    }

    return victim;
}

std::shared_ptr<ReplacementData>
AdaptiveBypassRP::instantiateEntry()
{
    return std::shared_ptr<ReplacementData>(new AdaptiveBypassReplData());
}

AdaptiveBypassRP*
AdaptiveBypassRPParams::create()
{
    return new AdaptiveBypassRP(this);
}
