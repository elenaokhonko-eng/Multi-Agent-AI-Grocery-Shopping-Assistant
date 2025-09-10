import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Save, Undo2, Settings2, Tags, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { loadUserProfile, saveUserProfile, loadUserProfileFromBackend } from "@/lib/user-profile";
import { DEFAULT_USER_PROFILE, UserProfile } from "@/types/user-profile";

const toList = (arr: string[]) => arr.join(", ");
const toArray = (s: string) =>
  s.split(",").map(x => x.trim()).filter(Boolean);

export default function UserProfilePage() {
  const { toast } = useToast();
  const [profile, setProfile] = useState<UserProfile>(loadUserProfile());
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => { setDirty(true); }, [profile]);

  // Load profile from backend on component mount
  useEffect(() => {
    const loadFromBackend = async () => {
      setLoading(true);
      try {
        const backendProfile = await loadUserProfileFromBackend();
        setProfile(backendProfile);
        setDirty(false);
      } catch (error) {
        console.warn("Failed to load from backend, using localStorage");
      } finally {
        setLoading(false);
      }
    };
    
    loadFromBackend();
  }, []);

  const totalDietFlags = useMemo(
    () => Object.values(profile.dietary_needs).filter(v => v === true).length,
    [profile.dietary_needs]
  );

  const save = async () => {
    setSaving(true);
    try {
      await saveUserProfile(profile);
      setDirty(false);
      toast({ 
        title: "Profile saved", 
        description: "Your preferences are updated and sent to the backend pipeline." 
      });
    } catch (error) {
      toast({ 
        title: "Save failed", 
        description: "Failed to save profile. Please try again.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const reset = () => {
    setProfile(loadUserProfile());
    setDirty(false);
  };

  const resetToDefaults = () => {
    setProfile(DEFAULT_USER_PROFILE);
    setDirty(true);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-3xl font-bold">User Profile</h1>
              <p className="text-muted-foreground">Tell the AI how to shop & deliver for you</p>
              {loading && (
                <p className="text-sm text-blue-600 flex items-center gap-2 mt-1">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Loading profile from backend...
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={reset} disabled={!dirty || saving}>
              <Undo2 className="mr-2 h-4 w-4" /> Revert
            </Button>
            <Button onClick={save} disabled={saving} className="bg-gradient-primary hover:opacity-90">
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Budget & Location */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5" /> Budget & Location
            </CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Budget Limit (LKR)</Label>
              <Input
                type="number"
                value={profile.budget_limit_lkr}
                onChange={(e) =>
                  setProfile({ ...profile, budget_limit_lkr: Number(e.target.value || 0) })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Location</Label>
              <Input
                type="text"
                placeholder="e.g., Colombo, Sri Lanka"
                value={profile.location || ""}
                onChange={(e) =>
                  setProfile({ ...profile, location: e.target.value })
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Dietary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Dietary Needs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {([
                ["vegetarian","Vegetarian"],
                ["vegan","Vegan"],
                ["gluten_free","Gluten-free"],
                ["dairy_free","Dairy-free"],
                ["organic_only","Organic only"],
                ["low_sodium","Low Sodium"],
                ["sugar_free","Sugar-free"],
                ["halal","Halal"],
                ["kosher","Kosher"],
              ] as const).map(([key,label]) => (
                <div key={key} className="flex items-center justify-between border rounded-xl px-3 py-2">
                  <Label>{label}</Label>
                  <Switch
                    checked={profile.dietary_needs[key]}
                    onCheckedChange={(v) =>
                      setProfile({
                        ...profile,
                        dietary_needs: { ...profile.dietary_needs, [key]: v },
                      })
                    }
                  />
                </div>
              ))}
            </div>

            <div className="mt-4 grid gap-2">
              <Label className="flex items-center gap-2">
                <Tags className="h-4 w-4" /> Allergies (comma separated)
              </Label>
              <Input
                placeholder="peanuts, shellfish, ..."
                value={toList(profile.dietary_needs.allergies)}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    dietary_needs: {
                      ...profile.dietary_needs,
                      allergies: toArray(e.target.value),
                    },
                  })
                }
              />
              {profile.dietary_needs.allergies.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {profile.dietary_needs.allergies.map(a => (
                    <Badge key={a} variant="secondary">{a}</Badge>
                  ))}
                </div>
              )}
            </div>

            <p className="text-xs text-muted-foreground mt-3">
              {totalDietFlags} dietary rules active.
            </p>
          </CardContent>
        </Card>

        {/* Brand preferences */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Brand Preferences</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Preferred brands (comma separated)</Label>
              <Input
                placeholder="Brand A, Brand B"
                value={toList(profile.brand_preferences.preferred_brands)}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    brand_preferences: {
                      ...profile.brand_preferences,
                      preferred_brands: toArray(e.target.value),
                    },
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Disliked brands (comma separated)</Label>
              <Input
                placeholder="Brand X, Brand Y"
                value={toList(profile.brand_preferences.disliked_brands)}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    brand_preferences: {
                      ...profile.brand_preferences,
                      disliked_brands: toArray(e.target.value),
                    },
                  })
                }
              />
            </div>

            <div className="flex items-center justify-between border rounded-xl px-3 py-2">
              <Label>Premium brands only</Label>
              <Switch
                checked={profile.brand_preferences.premium_brands_only}
                onCheckedChange={(v) =>
                  setProfile({
                    ...profile,
                    brand_preferences: {
                      ...profile.brand_preferences,
                      premium_brands_only: v,
                    },
                  })
                }
              />
            </div>

            <div className="flex items-center justify-between border rounded-xl px-3 py-2">
              <Label>Prioritize local brands</Label>
              <Switch
                checked={profile.brand_preferences.local_brands_priority}
                onCheckedChange={(v) =>
                  setProfile({
                    ...profile,
                    brand_preferences: {
                      ...profile.brand_preferences,
                      local_brands_priority: v,
                    },
                  })
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Loyalty & Stores */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Loyalty & Stores</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Preferred stores (comma separated domains or names)</Label>
              <Input
                placeholder="glowmark.lk, kapruka.com"
                value={toList(profile.loyalty_membership.preferred_stores)}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    loyalty_membership: {
                      ...profile.loyalty_membership,
                      preferred_stores: toArray(e.target.value),
                    },
                  })
                }
              />
              <p className="text-xs text-muted-foreground">
                Membership IDs & points can be managed in a future section.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Notes (optional)</Label>
              <Textarea placeholder="Any loyalty notes…" />
            </div>
          </CardContent>
        </Card>

        {/* Delivery */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Delivery Preferences</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Max delivery time (hours)</Label>
              <Input
                type="number"
                value={profile.delivery_preferences.max_delivery_time_hours}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    delivery_preferences: {
                      ...profile.delivery_preferences,
                      max_delivery_time_hours: Number(e.target.value || 0),
                    },
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Max delivery radius (km)</Label>
              <Input
                type="number"
                value={profile.delivery_preferences.max_delivery_radius_km}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    delivery_preferences: {
                      ...profile.delivery_preferences,
                      max_delivery_radius_km: Number(e.target.value || 0),
                    },
                  })
                }
              />
            </div>
            <div className="md:col-span-2 space-y-2">
              <Label>Preferred time slots (comma separated)</Label>
              <Input
                placeholder="09:00-12:00, 14:00-18:00"
                value={toList(profile.delivery_preferences.preferred_time_slots)}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    delivery_preferences: {
                      ...profile.delivery_preferences,
                      preferred_time_slots: toArray(e.target.value),
                    },
                  })
                }
              />
            </div>
            <div className="flex items-center justify-between border rounded-xl px-3 py-2">
              <Label>Avoid weekends</Label>
              <Switch
                checked={profile.delivery_preferences.avoid_weekends}
                onCheckedChange={(v) =>
                  setProfile({
                    ...profile,
                    delivery_preferences: {
                      ...profile.delivery_preferences,
                      avoid_weekends: v,
                    },
                  })
                }
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={resetToDefaults} disabled={saving}>
            Reset to defaults
          </Button>
          <Button onClick={save} disabled={saving} className="bg-gradient-primary hover:opacity-90">
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
