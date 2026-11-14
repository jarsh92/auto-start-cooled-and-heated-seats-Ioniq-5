package com.nemesis.coldstart;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.graphics.Rect;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=19, manifest=Config.NONE, qualifiers="w1280dp-h720dp-mdpi")
public class LayoutTest {
    public static class UiHarness extends MainActivity {
        String lastRequest;
        @Override void executeSeatAction(String name, String commands) { lastRequest=commands; }
    }
    private Button find(View v, String text) {
        if(v instanceof Button && ((Button)v).getText().toString().equals(text))return (Button)v;
        if(v instanceof ViewGroup) for(int i=0;i<((ViewGroup)v).getChildCount();i++){
            Button b=find(((ViewGroup)v).getChildAt(i),text);if(b!=null)return b;
        }
        return null;
    }
    private void check(int width,int height){
        UiHarness a=Robolectric.buildActivity(UiHarness.class).get();
        a.seatDrv=3; a.seatPass=2; a.ventDrv=3; a.ventPass=2;
        a.buildScreen();
        View root=((ViewGroup)a.findViewById(android.R.id.content)).getChildAt(0);
        root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
        root.layout(0,0,width,height);
        for(String label:new String[]{"Close","Heating","Ventilation","Settings","All Off · Both seats + steering wheel"}){
            Button b=find(root,label);assertNotNull(label,b);
            Rect r=new Rect(); b.getDrawingRect(r);((ViewGroup)root).offsetDescendantRectToMyCoords(b,r);
            System.out.println(label+": "+r.toShortString());
            assertTrue(label+" not laid out",r.width()>0&&r.height()>0);
            assertTrue(label+" extends below window: "+r.bottom+" > "+height,r.top>=0&&r.bottom<=height);
        }
        assertTrue("Heating test must have body space",a.heatTestBtn.getMeasuredHeight()>0);
        assertTrue("Scroll area must have room for controls", a.bodyScroll.getMeasuredHeight() >= 100);
        // Selection changes are not commands. Individual Apply sends one seat only.
        a.drvBtn.performClick();
        assertEquals(0,a.seatDrv); assertNull(a.lastRequest);
        assertEquals("Turn driver seat Off",a.applyDrvHeat.getText().toString());
        a.applyDrvHeat.performClick(); assertTrue(a.lastRequest.endsWith(" driver_heat 0"));
        a.applyPassHeat.performClick(); assertTrue(a.lastRequest.endsWith(" passenger_heat 2"));
        assertEquals(2,a.seatPass);
        find(root,"Settings").performClick();
        root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
        root.layout(0,0,width,height);
        assertTrue("Settings must open",a.settingsPage.getVisibility()==View.VISIBLE);
        find(root,"Ventilation").performClick();
        root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
        root.layout(0,0,width,height);
        assertTrue("Ventilation must open",a.ventPage.getVisibility()==View.VISIBLE);
        assertFalse("Settings must hide",a.settingsPage.getVisibility()==View.VISIBLE);
        a.applyDrvVent.performClick(); assertTrue(a.lastRequest.endsWith(" driver 3"));
        a.ventPassBtn.performClick(); a.ventPassBtn.performClick();
        assertEquals(0,a.ventPass);
        assertEquals("Turn passenger seat Off",a.applyPassVent.getText().toString());
        a.applyPassVent.performClick(); assertTrue(a.lastRequest.endsWith(" passenger 0"));
        a.finish();
    }
    @Test public void controlsFitHeadUnit(){check(1280,620);}
    @Test public void controlsFitShorterViewport(){check(1280,480);}
    @Test public void controlsFitWiderViewport(){check(1920,640);}
}
